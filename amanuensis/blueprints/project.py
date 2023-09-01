import flask
from wsgiref.util import request_uri

from cdislogging import get_logger

from amanuensis.resources.project import create, get_all
from amanuensis.resources.admin import get_by_code
from amanuensis.resources.fence import fence_get_users
from amanuensis.resources.request import get_request_state
from amanuensis.auth.auth import current_user, has_arborist_access
from amanuensis.errors import AuthError, InternalError
from amanuensis.schema import ProjectSchema
from amanuensis.config import config


# from amanuensis.auth import login_required, current_token
# from amanuensis.errors import Unauthorized, UserError, NotFound



blueprint = flask.Blueprint("projects", __name__)

logger = get_logger(__name__)

#given a set of states we can navigate up the tree
#{"REJECT", "APPROVED", ""}
def determine_status_code(project_requests_states):
    try:  
        states_flow_chart = {
            "DRAFT": [],
            "SUBMITTED": ["DRAFT"],
            "IN_REVIEW": ["SUBMITTED", "REVISION"],
            "REVISION": ["IN_REVIEW"],
            "APPROVED_WITH_FEEDBACK": ["IN_REVIEW"],
            "APPROVED": ["IN_REVIEW"],
            "REQUEST_CRITERIA_FINALIZED": ["APPROVED_WITH_FEEDBACK", "APPROVED"],
            "AGREEMENTS_NEGOTIATION": ["REQUEST_CRITERIA_FINALIZED"],
            "AGREEMENTS_EXECUTED": ["AGREEMENTS_NEGOTIATION"],
            "DATA_AVAILABLE": ["AGREEMENTS_EXECUTED"],
            "DATA_DOWNLOADED": ["DATA_AVAILABLE"],
            "REJECTED": ["IN_REVIEW"],
            "WITHDRAWAL": ["REVISION", "IN_REVIEW", "SUBMITTED", "DRAFT"], 
            #"PUBLISHED": ["DATA_DOWNLOADED"] is this a potentional state
        }
        seen = set()
        project_state_graph = ["WITHDRAWAL", "REJECTED", "DATA_DOWNLOADED"]
        this_project_state_heirarchy = []
        while project_state_graph and project_requests_states:
            current_state = project_state_graph.pop()
            if current_state not in seen:
                project_state_graph.extend(states_flow_chart[current_state])
            seen.add(current_state)

            if current_state in project_requests_states:
                project_requests_states.remove(current_state)
                this_project_state_heirarchy.append(current_state)

        if project_requests_states:
            raise InternalError("{project_request_states} are not valid state(s)")
        
        if not this_project_state_heirarchy:
            raise InternalError("no states were given")

        return {"status": this_project_state_heirarchy[-1]}

    except (KeyError, InternalError):
         logger.error(
            "Unable to load or find the consortium status"
         )
         raise InternalError("Unable to load or find the consortium status")       


@blueprint.route("/", methods=["GET"])
def get_projetcs():
    try:
        logged_user_id = current_user.id
        logged_user_email = current_user.username
    except AuthError:
        logger.warning("Unable to load or find the user, check your token")

    # special_user = [approver, admin]
    special_user = flask.request.args.get("special_user", None)
    # special_user = flask.request.get_json().get("special_user", None)
    if special_user and special_user == "admin" and not has_arborist_access(resource="/services/amanuensis", method="*"):
        raise AuthError(
                "The user is trying to access as admin but it's not an admin."
            )

    project_schema = ProjectSchema(many=True)
    projects = project_schema.dump(get_all(logged_user_id, logged_user_email, special_user))

    return_projects = []

    for project in projects:
        tmp_project = {}
        tmp_project["id"] = project["id"]
        tmp_project["name"] = project["name"]

        submitted_at = None
        completed_at = None
        project_status = None
        statuses_by_consortium = set()
        for request in project["requests"]:
            #TODO this should come from the get_all above and not make extra queries to the DB. 
            request_state = get_request_state(request["id"], flask.current_app.scoped_session())
            statuses_by_consortium.add(request_state.state.code)
            if not submitted_at:
                submitted_at = request["create_date"]

        project_status = determine_status_code(
            statuses_by_consortium
        )

        fence_users = fence_get_users(config=config, ids=[project["user_id"]])
        fence_users = fence_users["users"] if "users" in fence_users else []
        if len(fence_users) != 1:
            raise InternalError(
                "There can't be more or less than one user opening a project request."
            )

        tmp_project["researcher"] = {}
        tmp_project["researcher"]["id"] = fence_users[0]["id"]
        tmp_project["researcher"]["first_name"] = fence_users[0]["first_name"]
        tmp_project["researcher"]["last_name"] = fence_users[0]["last_name"]
        tmp_project["researcher"]["institution"] = fence_users[0]["institution"]

        tmp_project["status"] = get_by_code(project_status["status"]).name if project_status["status"] else "ERROR"
        tmp_project["submitted_at"] = submitted_at
        tmp_project["completed_at"] = project_status["completed_at"] if "completed_at" in project_status else None

        tmp_project["has_access"] = False
        if "associated_users_roles" in project:
            for associated_user_role in project["associated_users_roles"]:
                if associated_user_role["role"] == "DATA_ACCESS":
                    if logged_user_id == associated_user_role["associated_user"]["user_id"] or logged_user_email == associated_user_role["associated_user"]["email"]:
                        tmp_project["has_access"] = True
                        break

        return_projects.append(tmp_project)

    return flask.jsonify(return_projects)


@blueprint.route("/", methods=["POST"])
def create_project():
    """
    Create a data request project

    Returns a json object
    """
    try:
        logged_user_id = current_user.id
    except AuthError:
        logger.warning(
            "Unable to load or find the user, check your token"
        )


    associated_users_emails = flask.request.get_json().get("associated_users_emails", None)
    # if not associated_users_emails:
    #     raise UserError("You can't create a Project without specifying the associated_users that will access the data")

    name = flask.request.get_json().get("name", None)
    description = flask.request.get_json().get("description", None)
    institution = flask.request.get_json().get("institution", None)

    filter_set_ids = flask.request.get_json().get("filter_set_ids", None)

    # get the explorer_id from the querystring ex: https://portal-dev.pedscommons.org/explorer?id=1
    explorer_id = flask.request.args.get('explorer', default=1, type=int)

    project_schema = ProjectSchema()
    return flask.jsonify(
        project_schema.dump(
            create(
                logged_user_id,
                False,
                name,
                description,
                filter_set_ids,
                explorer_id,
                institution,
                associated_users_emails
            )
        )
    )
