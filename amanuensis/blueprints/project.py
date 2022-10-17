from wsgiref.util import request_uri
import flask
from flask_sqlalchemy_session import current_session

# from amanuensis.auth import login_required, current_token
# from amanuensis.errors import Unauthorized, UserError, NotFound
from amanuensis.resources.project import create, get_all
from amanuensis.resources.admin import get_by_code
from amanuensis.resources.fence import fence_get_users
from amanuensis.config import config
from amanuensis.auth.auth import current_user
from amanuensis.errors import AuthError, InternalError
from amanuensis.schema import ProjectSchema
from amanuensis.resources.request import get_request_state
from cdislogging import get_logger


blueprint = flask.Blueprint("projects", __name__)

logger = get_logger(__name__)


# cache = SimpleCache()

def determine_status_code(statuses_by_consortium):
    """
    Takes status codes from all the requests within a project and returns the project status based on their precedence.
    Example: if all request status are "APPROVED", then the status code will be "APPROVED".
    However, if one of the request status is "PENDING", and "PENDING" has higher precedence
    then the status code will be "PENDING".
    """
    try:
        overall_status = None
        overall_consortium = None
        overall_dist_to_end = None
        for status in statuses_by_consortium:
            ordered_statuses_by_consortium = list(config["CONSORTIUM_STATUS"][status["consortium"]]["CODES"])
            final_statuses = list(config["CONSORTIUM_STATUS"][status["consortium"]]["FINAL"])
            
            if status["status_code"] not in ordered_statuses_by_consortium:
                raise InternalError("{} not found in the config".format(status["status_code"]))

            approved_index = ordered_statuses_by_consortium.index("DATA_DELIVERED")
            index = ordered_statuses_by_consortium.index(status["status_code"])
            dist_to_end = approved_index - index

            if status["status_code"] in final_statuses:
                return {"status": status["status_code"], "completed_at": status["update_date"]} 

            if not overall_status or dist_to_end > overall_dist_to_end:
                overall_dist_to_end = dist_to_end
                overall_consortium = status["consortium"]
                overall_status = status["status_code"]

        return {"status": overall_status}

    except KeyError:
        logger.error(
            "Unable to load or find the consortium status, check your config file"
        )
        raise InternalError("Unable to load or find the consortium status, check your config file")


@blueprint.route("/", methods=["GET"])
def get_projetcs():
    try:
        logged_user_id = current_user.id
        logged_user_email = current_user.username
    except AuthError:
        logger.warning("Unable to load or find the user, check your token")

    # TODO assign this as a resource in arborist
    approver = flask.request.args.get("approver", None)

    project_schema = ProjectSchema(many=True)
    projects = project_schema.dump(get_all(logged_user_id, logged_user_email, approver))

    return_projects = []

    for project in projects:
        tmp_project = {}
        tmp_project["id"] = project["id"]
        tmp_project["name"] = project["name"]

        submitted_at = None
        completed_at = None
        project_status = None
        statuses_by_consortium = []
        for request in project["requests"]:
            #TODO this should come from the get_all above and not make extra queries to the DB. 
            request_state = get_request_state(request["id"])
            statuses_by_consortium.append({"status_code": request_state.code, "consortium": request["consortium_data_contributor"]["code"], "update_date": request_state.update_date})

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

        tmp_project["status"] = get_by_code(project_status["status"]).name
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


# DISABLE FOR NOW SINCE ONLY ADMIN CAN CREATE A PROJECT
# @blueprint.route("/", methods=["POST"])
# def create_project():
#     """
#     Create a search on the userportaldatamodel database

#     Returns a json object
#     """
#     try:
#         logged_user_id = current_user.id
#     except AuthError:
#         logger.warning(
#             "Unable to load or find the user, check your token"
#         )

#     # get the explorer_id from the querystring
#     explorer_id = flask.request.args.get('explorer', default=1, type=int)

#     name = flask.request.get_json().get("name", None)
#     description = flask.request.get_json().get("description", None)

#     #backward compatibility
#     search_ids = flask.request.get_json().get("search_ids", None)
#     filter_set_ids = flask.request.get_json().get("filter_set_ids", None)

#     if search_ids and not filter_set_ids:
#         filter_set_ids = search_ids

#     project_schema = ProjectSchema()
#     return flask.jsonify(project_schema.dump(create(logged_user_id, False, name, description, filter_set_ids, explorer_id)))
