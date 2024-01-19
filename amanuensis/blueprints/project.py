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
from userportaldatamodel.models import State, Transition
#TODO: userportaldatamodel.models needs to be updated to include transition
#from userportaldatamodel.transition import Transition


# from amanuensis.auth import login_required, current_token
# from amanuensis.errors import Unauthorized, UserError, NotFound



blueprint = flask.Blueprint("projects", __name__)

logger = get_logger(__name__)


# cache = SimpleCache()


def determine_status_code(this_project_requests_states):
    """
    Takes status codes from all the requests within a project and returns the project status based on their precedence.
    Example: if all request status are "APPROVED", then the status code will be "APPROVED".
    However, if one of the request status is "PENDING", and "PENDING" has higher precedence
    then the status code will be "PENDING".
    """
    #run BFS on state flow chart
    try: 
        #check if withdrawal or Rejected are a state
        if "WITHDRAWAL" in this_project_requests_states:
                return {"status": "WITHDRAWAL"}
            
        if "REJECTED" in this_project_requests_states:
            return {"status": "REJECTED"}
        
        with flask.current_app.db.session as session:
            seen_codes = set()
            overall_project_state = None
            #states_queue = [(id, code)]
            states_queue = [(session.query(State.id).filter(State.code == "PUBLISHED").all()[0], "PUBLISHED")]
            while states_queue and this_project_requests_states:
                #pull out data of current state
                current_state = states_queue.pop(0)
                if current_state[1] not in seen_codes:
                    #add state to seen
                    seen_codes.add(current_state[1])
                    #query parent states and add to queue
                    parent_states_code_id = session.query(Transition.state_src_id, State.code).join(
                                                            Transition, Transition.state_src_id == State.id
                                                        ).filter(
                                                            Transition.state_dst.has(id=current_state[0])
                                                        ).all()
                    states_queue.extend([state for state in parent_states_code_id])
                    #change overall project status if applicable
                    if current_state[1] in this_project_requests_states:
                        this_project_requests_states.remove(current_state[1])
                        if ((current_state[1] == "APPROVED" and overall_project_state == "APPROVED_WITH_FEEDBACK")    
                            or (current_state[1] == "REVISION") and overall_project_state == "SUBMITTED"):
                            continue
                        else:
                            overall_project_state = current_state[1]

            if this_project_requests_states:
                raise InternalError("{project_request_states} are not valid state(s)")

            return {"status": overall_project_state}

    except (KeyError, InternalError):
        #  logger.error(
        #     "Unable to load or find the consortium status"
        #  )
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
        consortiums = set()
        for request in project["requests"]:
            statuses_by_consortium.add(request['states'][-1]["code"])
            consortiums.add(request['consortium_data_contributor']['code'])

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
                if associated_user_role["role"]["code"] == "DATA_ACCESS":
                    if logged_user_id == associated_user_role["associated_user"]["user_id"] or logged_user_email == associated_user_role["associated_user"]["email"]:
                        tmp_project["has_access"] = True
                        break
        
        tmp_project["consortia"] = list(consortiums)
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
