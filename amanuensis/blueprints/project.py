import flask
from wsgiref.util import request_uri

from cdislogging import get_logger

from amanuensis.resources.project import create
from amanuensis.resources.fence import fence_get_users
from amanuensis.auth.auth import current_user, has_arborist_access
from amanuensis.errors import AuthError, InternalError, UserError
from amanuensis.schema import ProjectSchema
from amanuensis.config import config
from datetime import datetime
from userportaldatamodel.models import State, Transition
from amanuensis.resources.userdatamodel.associated_users import create_associated_user, update_associated_user
from amanuensis.resources.userdatamodel.project import get_projects
from amanuensis.resources.userdatamodel.request_has_state import get_request_states
from amanuensis.resources.request import calculate_overall_project_state
from amanuensis.resources.userdatamodel.state import get_states

#TODO: userportaldatamodel.models needs to be updated to include transition
#from userportaldatamodel.transition import Transition


# from amanuensis.auth import login_required, current_token
# from amanuensis.errors import Unauthorized, UserError, NotFound



blueprint = flask.Blueprint("projects", __name__)

logger = get_logger(__name__)



# cache = SimpleCache()



@blueprint.route("/", methods=["GET"])
def get_projetcs():
    try:
        logged_user_id = current_user.id
        logged_user_email = current_user.username
    except AuthError:
        logger.warning("Unable to load or find the user, check your token")

    #add user_id from fence if this is the users first time logging in
    with flask.current_app.db.session as session:
        associated_user = create_associated_user(session, logged_user_email, user_id=logged_user_id)
        if not associated_user.user_id:
            update_associated_user(session, associated_user, new_user_id=logged_user_id)
        
        project_schema = ProjectSchema(many=True)
        # special_user = [approver, admin]
        special_user = flask.request.args.get("special_user", None)
        is_admin = has_arborist_access(resource="/services/amanuensis", method="*")
        # special_user = flask.request.get_json().get("special_user", None)
        if special_user and special_user == "admin":
            if is_admin:
                projects = get_projects(session)
            else:
                raise AuthError(
                        "The user is trying to access as admin but it's not an admin." 
                )
        else:
            projects = get_projects(session, associated_user_email=logged_user_email)


        
        

        return_projects = []

        for project in projects:
            tmp_project = {}
            tmp_project["id"] = project.id
            tmp_project["name"] = project.name

            project_status = None
            request_states = get_request_states(session, project_id=project.id, filter_out_depricated=True, latest=True)
            statuses_by_consortium = {request_state.state.code for request_state in request_states}
            consortiums = [request_state.request.consortium_data_contributor.code for request_state in request_states]
            
            submitted_at = request_states[0].create_date if request_states else None

            project_status = calculate_overall_project_state(
                session, this_project_requests_states=statuses_by_consortium
            )

            fence_users = fence_get_users(ids=[project.user_id])
            fence_users = fence_users["users"] if "users" in fence_users else []
            if not fence_users:
                logger.error(
                    "ERROR: Unable to find user in fence. check with the PCDC admin"
                )
                continue


            tmp_project["researcher"] = {}
            tmp_project["researcher"]["id"] = fence_users[0]["id"]
            tmp_project["researcher"]["first_name"] = fence_users[0]["first_name"]
            tmp_project["researcher"]["last_name"] = fence_users[0]["last_name"]
            tmp_project["researcher"]["institution"] = fence_users[0]["institution"]
            #TODO in data-portal look to change the button criteria from "DATA AVAILABLE" to "DATA_AVAILABLE" this will remove this call below
            tmp_project["status"] = get_states(session, code=project_status["status"], many=False, filter_out_depricated=True).name if project_status["status"] else "ERROR"
            tmp_project["submitted_at"] = submitted_at
            tmp_project["completed_at"] = project_status["completed_at"] if "completed_at" in project_status else None

            tmp_project["has_access"] = False
            for user in project.associated_users_roles:
                if user.role and user.role.code == "DATA_ACCESS" and user.active and (user.associated_user.user_id == logged_user_id or user.associated_user.email == logged_user_email):
                    tmp_project["has_access"] = True
                    break
            tmp_project["consortia"] = list(consortiums)
            return_projects.append(tmp_project)

        session.commit()

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
        raise UserError("a filter-set id is required field")
    
    # get the explorer_id from the querystring ex: https://portal-dev.pedscommons.org/explorer?id=1
    explorer_id = flask.request.args.get('explorer', default=1, type=int)

    project_schema = ProjectSchema()

    with flask.current_app.db.session as session:
        return flask.jsonify(
            project_schema.dump(
                create(
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
            )
        )
