import flask
from collections import defaultdict
from datetime import datetime

from cdislogging import get_logger

from amanuensis.resources.project import create
from amanuensis.resources.fence import fence_get_users
from amanuensis.auth.auth import current_user, has_arborist_access
from amanuensis.errors import Forbidden, UserError, AuthNError
from amanuensis.schema import ProjectSchema
from amanuensis.resources.userdatamodel.associated_users import create_associated_user, update_associated_user
from amanuensis.resources.userdatamodel.project import get_projects,get_projects_page, count_projects
from amanuensis.resources.userdatamodel.request_has_state import get_request_states
from amanuensis.resources.request import calculate_overall_project_state
from amanuensis.resources.userdatamodel.state import get_states
from amanuensis.utils.pagination import parse_page_and_per_page, build_link_header

blueprint = flask.Blueprint("projects", __name__)
logger = get_logger(__name__)

DEFAULT_PER_PAGE = 30
MAX_PER_PAGE = 100


def _parse_date(value):
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise UserError(f"Invalid date '{value}', expected YYYY-MM-DD or MM/DD/YYYY")

def _enrich_projects(session, projects, logged_user_id, logged_user_email):
    """
    Attach the derived (non-DB) fields to a batch of Project rows in O(1)
    extra queries/HTTP calls. Returns a list of
    (project_dict, status_code) tuples - the code is kept alongside (rather
    than in the dict) so callers can filter on it without it leaking into
    the API response.
    """
    if not projects:
        return []

    project_ids = [p.id for p in projects]

    all_request_states = get_request_states(
        session, project_id=project_ids, filter_out_depricated=True, latest=True
    )
    request_states_by_project = defaultdict(list)
    for rs in all_request_states:
        request_states_by_project[rs.request.project_id].append(rs)

    state_name_by_code = {
        s.code: s.name for s in get_states(session, many=True, filter_out_depricated=True) # this. may be many=False
    }

    user_ids = list({p.user_id for p in projects if p.user_id is not None})
    fence_response = fence_get_users(ids=user_ids) if user_ids else {}
    fence_users_by_id = {u["id"]: u for u in fence_response.get("users", [])}

    enriched = []
    for project in projects:
        request_states = request_states_by_project.get(project.id, [])
        statuses_by_consortium = {rs.state.code for rs in request_states}
        consortiums = [rs.request.consortium_data_contributor.code for rs in request_states]
        # NOTE: pre-existing behaviour - takes the first request_state's
        # create_date rather than the earliest. Worth a separate look if
        # "submitted_at" is meant to be the original submission date.
        submitted_at = request_states[0].create_date if request_states else None

        project_status = calculate_overall_project_state(
            session, this_project_requests_states=statuses_by_consortium
        )

        fence_user = fence_users_by_id.get(project.user_id)
        if not fence_user:
            logger.error("ERROR: Unable to find user in fence. check with the PCDC admin")
            continue

        status_code = project_status["status"]
        tmp_project = {
            "id": project.id,
            "name": project.name,
            "researcher": {
                "id": fence_user["id"],
                "first_name": fence_user["first_name"],
                "last_name": fence_user["last_name"],
                "institution": fence_user["institution"],
            },
            "status": state_name_by_code.get(status_code, "ERROR") if status_code else "ERROR",
            "submitted_at": submitted_at,
            "completed_at": project_status.get("completed_at"),
            "description": project.description,
            "approved_url_present": bool(project.approved_url),
            "has_access": False,
            "consortia": list(consortiums),
        }
        for user in project.associated_users_roles:
            if user.role and user.role.code == "DATA_ACCESS" and user.active and (
                user.associated_user.user_id == logged_user_id or user.associated_user.email == logged_user_email
            ):
                tmp_project["has_access"] = True
                break

        enriched.append((tmp_project, status_code))

    return enriched

def _apply_post_filters(enriched, selected_statuses, submitted_at_start, submitted_at_end):
    if selected_statuses:
        selected = set(selected_statuses)
        enriched = [(p, code) for (p, code) in enriched if p["status"] in selected or code in selected]
    if submitted_at_start:
        enriched = [(p, code) for (p, code) in enriched if p["submitted_at"] and p["submitted_at"] >= submitted_at_start]
    if submitted_at_end:
        enriched = [(p, code) for (p, code) in enriched if p["submitted_at"] and p["submitted_at"] <= submitted_at_end]
    return enriched
    


#TODO when / if the project table gets a ton of record and this doesn't perform well we will need to add  status/last_submitted_at column on Project that gets updated whenever create_request_state runs, so filtering/sorting/pagination can all happen in one SQL query again.
@blueprint.route("/", methods=["GET"])
def get_projetcs():
    try:
        logged_user_id = current_user.id
        logged_user_email = current_user.username
    except AuthNError:
        raise AuthNError("Your session has expired. Please log in again to continue.")

    pagination = parse_page_and_per_page(DEFAULT_PER_PAGE, MAX_PER_PAGE)

    special_user = flask.request.args.get("special_user", None)
    project_id = flask.request.args.get("id", type=int)
    name = flask.request.args.get("name")
    description = flask.request.args.get("description")
    selected_researcher_ids = flask.request.args.getlist("researcher_id")
    selected_consortiums = flask.request.args.getlist("consortiums")
    selected_statuses = flask.request.args.getlist("status")
    raw_submitted_start = flask.request.args.get("submitted_at_start")
    raw_submitted_end = flask.request.args.get("submitted_at_end")
    submitted_at_start = _parse_date(raw_submitted_start)
    submitted_at_end = _parse_date(raw_submitted_end)

    # status/submitted_at aren't real columns - filtering on either means we
    # have to compute the derived fields for every DB-matched candidate
    # *before* slicing a page, or the page contents and "total" drift apart.
    needs_post_filtering = bool(selected_statuses or submitted_at_start or submitted_at_end)

    with flask.current_app.db.session as session:
        associated_user = create_associated_user(session, logged_user_email, user_id=logged_user_id)
        if not associated_user.user_id:
            update_associated_user(session, associated_user, new_user_id=logged_user_id)

        is_admin = has_arborist_access(resource="/services/amanuensis", method="*")
        if special_user and special_user == "admin":
            if not is_admin:
                raise Forbidden("You do not have the correct permissions to access all projects.")
            scope_filters = {}
        else:
            scope_filters = {"associated_user_email": logged_user_email}

        db_filters = dict(
            id=project_id,
            name_contains=name,
            description_contains=description,
            researcher_ids=selected_researcher_ids or None,
            consortiums=selected_consortiums or None,
            **scope_filters,
        )

        if pagination is not None:
            page, per_page = pagination
            offset = (page - 1) * per_page
        else:
            page = per_page = offset = None

        if needs_post_filtering:
            candidates = get_projects(session, **db_filters)
            enriched = _enrich_projects(session, candidates, logged_user_id, logged_user_email)
            enriched = _apply_post_filters(enriched, selected_statuses, submitted_at_start, submitted_at_end)
            total = len(enriched)
            page_slice = enriched[offset: offset + per_page] if pagination is not None else enriched
        else:
            limit = per_page if pagination is not None else None
            page_of_projects = get_projects_page(session, offset=offset, limit=limit, **db_filters)
            total = count_projects(session, **db_filters) if pagination is not None else None
            page_slice = _enrich_projects(session, page_of_projects, logged_user_id, logged_user_email)

        return_projects = [project for project, _status_code in page_slice]
        session.commit()

    response = flask.jsonify(return_projects)
    if pagination is not None:
        link = build_link_header(
            page, per_page, total,
            extra_query_params={
                "special_user": special_user,
                "id": project_id,
                "name": name,
                "description": description,
                "researcher_id": selected_researcher_ids,
                "consortiums": selected_consortiums,
                "status": selected_statuses,
                "submitted_at_start": raw_submitted_start,
                "submitted_at_end": raw_submitted_end,
            },
        )
        response.headers["Link"] = link
    return response


@blueprint.route("/", methods=["POST"])
def create_project():
    """
    Create a data request project

    Returns a json object
    """
    try:
        logged_user_id = current_user.id
    except AuthNError:
        raise AuthNError("Your session has expired. Please log in again to continue.")

    associated_users_emails = flask.request.get_json().get("associated_users_emails", None)
    # if not associated_users_emails:
    #     raise UserError("You can't create a Project without specifying the associated_users that will access the data")

    name = flask.request.get_json().get("name", None)

    if not name:
        raise UserError("name is a required field")

    description = flask.request.get_json().get("description", None)

    if not description:
        raise UserError("description is a required field")

    institution = flask.request.get_json().get("institution", None)

    if not institution:
        raise UserError("institution is a required field")

    filter_set_ids = flask.request.get_json().get("filter_set_ids", None)

    if not filter_set_ids:
        raise UserError("an id of a filter-set is required field")

    # get the explorer_id from the querystring ex: https://portal-dev.pedscommons.org/explorer?id=1
    explorer_id = flask.request.args.get('explorer', default=1, type=int)

    project_schema = ProjectSchema()

    with flask.current_app.db.session as session:
        new_project = create(
            session,
            logged_user_id,
            False,
            name,
            description,
            filter_set_ids,
            explorer_id,
            institution,
            associated_users_emails
        )
        session.refresh(new_project)
        return flask.jsonify(project_schema.dump(new_project))
