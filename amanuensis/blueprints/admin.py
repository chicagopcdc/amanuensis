"""
Blueprints for administation of the userdatamodel database and the storage
solutions. Operations here assume the underlying operations in the interface
will maintain coherence between both systems.
"""
import functools
from datetime import datetime
from cdiserrors import APIError
from flask import request, jsonify, Blueprint, current_app
from cdislogging import get_logger

from amanuensis.auth.auth import check_arborist_auth, current_user, has_arborist_access
from amanuensis.errors import UserError, AuthError
from amanuensis.resources.institution import get_background
from amanuensis.resources import project
from amanuensis.resources.userdatamodel.request_has_state import create_request_state
from amanuensis.resources.userdatamodel.request import get_requests
from amanuensis.resources.userdatamodel.project import update_project
from amanuensis.resources.userdatamodel.state import create_state, get_states
from amanuensis.resources.userdatamodel.consortium_data_contributor import create_consortium
from amanuensis.resources.userdatamodel.search import create_filter_set, get_filter_sets
from amanuensis.resources.request import change_request_state, project_requests_from_filter_sets
from amanuensis.resources.userdatamodel.associated_user_roles import get_associated_user_roles
from amanuensis.resources.userdatamodel.project_has_associated_user import get_project_associated_users, update_project_associated_user
from amanuensis.resources.userdatamodel.associated_users import get_associated_users
from amanuensis.resources.associated_user import add_associated_users, remove_associated_user
from amanuensis.resources.userdatamodel.project import get_projects
from amanuensis.resources.userdatamodel.notification import get_notifications, update_notification
from amanuensis.resources.userdatamodel.notification_log import create_notification_log, update_notification_log, get_notification_logs
from amanuensis.resources.fence import fence_get_all_users
from amanuensis.resources.userdatamodel.project_has_search import get_project_searches

from amanuensis.schema import (
    ProjectSchema,
    StateSchema,
    RequestSchema,
    ConsortiumDataContributorSchema,
    AssociatedUserSchema,
    SearchSchema,
    AssociatedUserRolesSchema,
    ProjectAssociatedUserSchema,
    NotificationSchema,
    NotificationLogSchema
)

logger = get_logger(__name__)

blueprint = Blueprint("admin", __name__)


def debug_log(function):
    """Output debug information to the logger for a function call."""
    argument_names = list(function.__code__.co_varnames)

    @functools.wraps(function)
    def write_log(*args, **kwargs):
        argument_values = (
            "{} = {}".format(arg, value)
            for arg, value in list(zip(argument_names, args)) + list(kwargs.items())
        )
        msg = function.__name__ + "\n\t" + "\n\t".join(argument_values)
        logger.debug(msg)
        return function(*args, **kwargs)

    return write_log

@blueprint.route("/project/force-state-change", methods=["POST"])
@check_arborist_auth(resource="/services/amanuensis", method="*")
def force_state_change():
    """
    used to undo errors, hide from UI
    """
    project_id = request.get_json().get("project_id", None)
    state_id = request.get_json().get("state_id", None)
    consortiums = request.get_json().get("consortiums", None)

    if not state_id or not project_id:
        raise UserError("There are missing params.")
    
    with current_app.db.session as session:
        requests = get_requests(session, project_id=project_id, consortiums=consortiums)

        new_states = []

        for request_obj in requests:
            new_state = create_request_state(session, request_obj.id, state_id)
            new_states.append(new_state)

        request_schema = RequestSchema(many=True)
        session.commit()
        return jsonify(
            request_schema.dump(new_states)
        )

        

@blueprint.route("/delete-project", methods=["DELETE"])
@check_arborist_auth(resource="/services/amanuensis", method="*")
def delete_project():
    project_id = request.get_json().get("project_id", None)
    if not project_id:
        raise UserError("A project_id is required for this endpoint.")
    

    with current_app.db.session as session:

        project_schema = ProjectSchema()

        project = update_project(session, project_id, delete=True)

        session.commit()

        return jsonify(project_schema.dump(project))


@blueprint.route("/upload-file", methods=["POST"])
@check_arborist_auth(resource="/services/amanuensis", method="*")
# @debug_log
def upload_file():
    """
    Generate presigned URL to upload file

    update approved_url with url generated from the uploaded file
    """

    key = request.get_json().get("key", None)
    project_id = request.get_json().get("project_id", None)
    
    #optional 
    expires = request.get_json().get("expires", None)
    
    if any(param is None for param in [key, project_id]):
            raise UserError("One or more required parameters are missing")
    
    with current_app.db.session as session:

        url = project.upload_file(session, key, project_id, expires)

        session.commit()

        return jsonify(url)


@blueprint.route("/states", methods=["POST"])
@check_arborist_auth(resource="/services/amanuensis", method="*")
# @debug_log
def add_state():
    """
    Create a new state

    Returns a json object
    """

    name = request.get_json().get("name", None)
    code = request.get_json().get("code", None)

    state_schema = StateSchema()
    with current_app.db.session as session:
        state = create_state(session, name, code)

        session.commit()

        return jsonify(state_schema.dump(state))


@blueprint.route("/consortiums", methods=["POST"])
@check_arborist_auth(resource="/services/amanuensis", method="*")
# @debug_log
def add_consortium():
    """
    Create a new state

    Returns a json object
    """

    name = request.get_json().get("name", None)
    code = request.get_json().get("code", None)

    consortium_schema = ConsortiumDataContributorSchema()

    with current_app.db.session as session:
        consortium = create_consortium(session, name, code)

        session.commit()

        return jsonify(consortium_schema.dump(consortium))


@blueprint.route("/states", methods=["GET"])
def get_state():
    """
    Create a new state

    Returns a json object
    """

    state_schema = StateSchema(many=True)

    with current_app.db.session as session:
        states = get_states(session, filter_out_depricated=True)

        return jsonify(state_schema.dump(states))

#TODO we should deprecate these filter-set routes and move them to the filter-set blueprint
#and add the is_admin and user_id params and then check the token if those are present
@blueprint.route("/filter-sets", methods=["POST"])
@check_arborist_auth(resource="/services/amanuensis", method="*")
# @debug_log
def create_search():
    """
    Create a search on the userportaldatamodel database

    Returns a json object
    """
    user_id = request.get_json().get("user_id", None)

    #TODO check it is present in fence

    if not user_id:
        raise UserError("Missing user_id in the payload")



    # get the explorer_id from the querystring
    # explorer_id = flask.request.args.get('explorerId', default=1, type=int)

    name = request.get_json().get("name", None)
    graphql_object = request.get_json().get("filters", {})
    description = request.get_json().get("description", None)
    ids_list = request.get_json().get("ids_list", None)

    with current_app.db.session as session:
        new_filter_set = create_filter_set(
            session,
            logged_user_id=user_id,
            is_amanuensis_admin=True, 
            explorer_id=None, 
            name=name, 
            description=description, 
            filter_object=None,
            ids_list=ids_list,
            graphql_object=graphql_object 
        )
    
        search_schema = SearchSchema()

        session.commit()

        return search_schema.dump(new_filter_set)

    
@blueprint.route("/filter-sets/user", methods=["GET"])
@check_arborist_auth(resource="/services/amanuensis", method="*")
# @debug_log
def get_search_by_user_id():    
    """
    Returns a json object
    """
    user_id = request.get_json().get("user_id", None)
    include_deleted = request.get_json().get("include_deleted", False)
    if not user_id:
        raise UserError("Missing user_id in the payload")
    # name = request.get_json().get("name", None)
    # search_id = request.get_json().get("search_id", None)
    # explorer_id = request.get_json().get('explorer_id', None)
    with current_app.db.session as session:
        filter_sets = [
            {
                "name": s.name, 
                "id": s.id, 
                "description": s.description, 
                "filters": s.filter_object, 
                "ids": s.ids_list
            } for s in get_filter_sets(session, user_id=user_id, filter_by_source_type=False, filter_by_active=(not include_deleted))
        ]


    return jsonify({"filter_sets": filter_sets})

@blueprint.route("/run-csl-verification", methods=["GET"])
#@check_arborist_auth(resource="/services/amanuensis", method = "*")
def screen_institution():
    name = request.args.get('name', default = None)
    fuzzy_name = request.args.get('fuzzy_name', default = None)
    if(name == None):
        raise UserError("Name of an Aircraft, Entity, Individual, or Vessel is needed in the name argument in the url")
    res = get_background(name, fuzzy_name)
    try:
        total = int(res["total"])
    except:
        raise APIError("Possible change to or error with CSL api, see https://developer.trade.gov/api-details#api=consolidated-screening-list")
    if(total == 50):
        logger.warning("The API only returns 50 results at a time, but more results match the search. If searching for one particular institution you may need to be more specific about the name")

    return jsonify(res)

@blueprint.route("/projects", methods=["POST"])
@check_arborist_auth(resource="/services/amanuensis", method="*")
# @debug_log
#TODO if we are releasing the other project create endpoint then we should deprecate this
#and check the auth in the other endpoint similar to project get endpoint
#since the code in both endpoints is practically the same
#the only difference is an admin can create a project for any user
def create_project():
    """
    Create a search on the userportaldatamodel database

    Returns a json object
    """
    user_id = request.get_json().get("user_id", None)
    if not user_id:
        raise UserError(
            "You can't create a Project without specifying the user the project will be assigned to."
        )

    #TODO check if user exists in Fence

    associated_users_emails = request.get_json().get("associated_users_emails", None)
    # if not associated_users_emails:
    #     raise UserError("You can't create a Project without specifying the associated_users that will access the data")

    name = request.get_json().get("name", None)

    if not name:
        raise UserError("name is a required field")
    
    description = request.get_json().get("description", None)

    if not description:
        raise UserError("description is a required field")
    
    institution = request.get_json().get("institution", None)

    if not institution:
        raise UserError("institution is a required field")

    filter_set_ids = request.get_json().get("filter_set_ids", None)

    if not filter_set_ids:
        raise UserError("a filter-set is required to create a project")

    with current_app.db.session as session:

        project_schema = ProjectSchema()
        new_project = project.create(
                    session,
                    user_id,
                    True,
                    name,
                    description,
                    filter_set_ids,
                    None,
                    institution,
                    associated_users_emails
                )
        
        session.commit()

        return jsonify(
            project_schema.dump(
                new_project
            )
        )


@blueprint.route("/projects", methods=["PUT"])
@check_arborist_auth(resource="/services/amanuensis", method="*")
# @debug_log
def update_project_attributes():
    """
    Update a project attributes

    Returns a json object
    """
    #TODO we should deprecate this endpoint or change it to update the project attributes 
    #approved url and filter_set_ids should be done through the other endpoints
    project_id = request.get_json().get("project_id", None)
    if not project_id:
        raise UserError("A project_id is required for this endpoint.")

    approved_url = request.get_json().get("approved_url", None)
    filter_set_ids = request.get_json().get("filter_set_ids", None)

    project_schema = ProjectSchema()
    with current_app.db.session as session:

        project = update_project(session, id=project_id, approved_url=approved_url)

        session.commit()

        return jsonify(
            project_schema.dump(project)
        )


@blueprint.route("/projects/state", methods=["POST"])
@check_arborist_auth(resource="/services/amanuensis", method="*")
# @debug_log
def update_project_state():
    """
    Create a new state

    Returns a json object
    """
    project_id = request.get_json().get("project_id", None)
    state_id = request.get_json().get("state_id", None)
    consortiums = request.get_json().get("consortiums", None)

    if consortiums and not isinstance(consortiums, list):
        consortiums = [consortiums]

    if not state_id or not project_id:
        raise UserError("There are missing params.")

    request_schema = RequestSchema(many=True)

    with current_app.db.session as session:

        request_state = change_request_state(session, project_id=project_id, state_id=state_id, consortium_list=consortiums)

        session.commit()


        return jsonify(
            request_schema.dump(request_state)
        )

@blueprint.route("/all_associated_user_roles", methods=["GET"])
@check_arborist_auth(resource="/services/amanuensis", method="*")
def get_all_associated_user_roles():
    associated_user_roles_schema = AssociatedUserRolesSchema(many=True)
    with current_app.db.session as session:
        return associated_user_roles_schema.dump(get_associated_user_roles(session))

@blueprint.route("/remove_associated_user_from_project", methods=["DELETE"])
@check_arborist_auth(resource="/services/amanuensis", method="*")
def delete_user_from_project():
    associated_user_id = request.get_json().get("user_id", None)
    associated_user_email = request.get_json().get("email", None)
    if not associated_user_id and not associated_user_email:
        raise UserError("A user_id and or an associated_user_email is required for this endpoint.")
    project_id = request.get_json().get("project_id", None)
    if not project_id:
        raise UserError("A project is nessary for this endpoint")

    with current_app.db.session as session:

        project_user = remove_associated_user(session, project_id, user_id=associated_user_id, email=associated_user_email)
        project_associated_user_schema = ProjectAssociatedUserSchema()
        session.commit()
        return project_associated_user_schema.dump(project_user)


@blueprint.route("/associated_user_role", methods=["PUT"])
@check_arborist_auth(resource="/services/amanuensis", method="*")
# @debug_log
def update_associated_user_role():
    """
    Update a project attributes

    Returns a json object
    """
    associated_user_id = request.get_json().get("user_id", None)
    associated_user_email = request.get_json().get("email", None)
    if not associated_user_id and not associated_user_email:
        raise UserError("A user_id and or an associated_user_email is required for this endpoint.")

    project_id = request.get_json().get("project_id", None)
    if not project_id:
        raise UserError("A project is nessary for this endpoint")
    role = request.get_json().get("role", None)     
    if not role:
        raise UserError("A role is required for this endpoint")

    with current_app.db.session as session:
        project_associated_user_schema = ProjectAssociatedUserSchema()
        ROLE = get_associated_user_roles(session, code=role, many=False, throw_not_found=True)
        user = get_associated_users(session, email=associated_user_email, user_id=associated_user_id,  many=False, throw_not_found=True)

        project_user = update_project_associated_user(session, associated_user_id=user.id, project_id=project_id,  role_id=ROLE.id)

        session.commit()

        return project_associated_user_schema.dump(project_user)


@blueprint.route("/associated_user", methods=["POST"])
@check_arborist_auth(resource="/services/amanuensis", method="*")
# @debug_log
def add_associated_user():
    """
    Update a project attributes
    users: [{project_id: "", id: "", email: ""},{}]

    Returns a json object
    """
    users = request.get_json().get("users", None)
    role = request.get_json().get("role", None)
    if not users:
        raise UserError("The body should be in the following format: [{project_id: \"\", id: \"\", email: \"\"},...] ")

    project_associated_user_schema = ProjectAssociatedUserSchema(many=True)

    with current_app.db.session as session:

        users = add_associated_users(session, users, role)

        session.commit()

        return project_associated_user_schema.dump(users)


@blueprint.route("/projects_by_users/<user_id>/<user_email>", methods=["GET"])
@check_arborist_auth(resource="/services/amanuensis", method="*")
def get_projetcs_by_user_id(user_id, user_email):
    #TODO we can deprecate the user_id part of this endpoint
    # the email is better cause there isnt a gurantee that the user_id is in the DB
    project_schema = ProjectSchema(many=True)
    with current_app.db.session as session:
        projects = get_projects(session, associated_user_email=user_email, many=True)
        return jsonify(project_schema.dump(projects))


@blueprint.route("/copy-search-to-user", methods=["POST"])
@check_arborist_auth(resource="/services/amanuensis", method="*")
def copy_search_to_user():
    """
    Given a search id from the searches saved by the admin and 
    a user_id picked among the list of all users, copy the search to the user domain.

    Returns a json object
    """
    try:
        logged_user_id = current_user.id
    except AuthError:
        logger.warning("Unable to load or find the user, check your token")


    filterset_id = request.get_json().get("filtersetId", None)

    if filterset_id is None:
        raise UserError("a filter-set id is required for this endpoint")
    
    user_id = request.get_json().get("userId", None)
    
    if user_id is None:
        raise UserError("a user id is required for this endpoint")


    search_schema = SearchSchema()
    # return flask.jsonify(search_schema.dump(filterset.copy_filter_set_to_user(filterset_id, logged_user_id, user_id)))
    with current_app.db.session as session:
        filterset = get_filter_sets(session, id=filterset_id, filter_by_source_type=False, many=False, throw_not_found=True)

        search_to_user = create_filter_set(
            session,
            logged_user_id=user_id,
            is_amanuensis_admin=True,
            explorer_id=filterset.filter_source_internal_id,
            name=filterset.name,
            description=filterset.description,
            filter_object=filterset.filter_object,
            ids_list=filterset.ids_list,
            graphql_object=filterset.graphql_object
        )

        session.commit()

        return jsonify(search_schema.dump(search_to_user))

@blueprint.route("/copy-search-to-project", methods=["POST"])
@check_arborist_auth(resource="/services/amanuensis", method="*")
def copy_search_to_project():
    """
    Given a search id from the searches saved by the admin and a project_id 
    assign this search to the related project

    Returns a json object
    """

    filterset_id = request.get_json().get("filtersetId", None)
    project_id = request.get_json().get("projectId", None)

    if not filterset_id:
        raise UserError("a filter-set id is required for this endpoint")
    project_schema = ProjectSchema()
    with current_app.db.session as session:
        
        copy_search_to_project = project_requests_from_filter_sets(session, filter_set_ids=filterset_id, project_id=project_id)

        session.commit()

        return jsonify(project_schema.dump(copy_search_to_project))
    # return flask.jsonify(project.update_project_searches(logged_user_id, project_id, filterset_id))


@blueprint.route("/project_users/<project_id>", methods=["GET"])
@check_arborist_auth(resource="/services/amanuensis", method="*")
def get_project_users(project_id):
    with current_app.db.session as session:
        users = get_project_associated_users(session, project_id, many=True)

        return jsonify([{"email": user.associated_user.email, "role": user.role.code} for user in users])



@blueprint.route("/create-notification", methods=["POST"])
@check_arborist_auth(resource="/services/amanuensis", method="*")
def add_new_notification():
    
    message = request.get_json().get("message", None)
    expire_date = request.get_json().get("expire_date", None)
    if not message:
        raise UserError("A message is required for this endpoint")
    if not expire_date:
        raise UserError("An expire date is required for this endpoint")
    
    try:
        datetime.strptime(expire_date, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        raise UserError("A valid datetime is required for this endpoint '%Y-%m-%d %H:%M:%S.%f'")

    with current_app.db.session as session:

        notification_schema = NotificationLogSchema()
        new_notification = create_notification_log(session, message, expire_date)
        session.commit()

        return notification_schema.dump(new_notification)


@blueprint.route("/notifications", methods=["GET"])
@check_arborist_auth(resource="/services/amanuensis", method="*")
def get_notification():
    
    user_id = request.args.get("user_id", type=int)
    notification_log_id = request.args.get("notification_log_id", type=int)
    message = request.args.get("message", type=str)
    seen = request.args.get("seen", type=bool)


    if seen is not None:
        filter_by_seen = True
    else:
        filter_by_seen = False


    with current_app.db.session as session:

        if user_id:

            notification_schema = NotificationSchema(many=True)

            notifications = get_notifications(
                                session, 
                                user_id=user_id, 
                                notification_log_id=notification_log_id, 
                                seen=seen,
                                filter_for_seen=filter_by_seen, 
                                many=True
                            )
        
            return notification_schema.dump(notifications)

        else:

            notification_log_schema = NotificationLogSchema(many=True)

            notifications = get_notification_logs(
                                session,  
                                ids=notification_log_id, 
                                messages=message,
                                expired=False,
                                many=True
                            )
        
            return notification_log_schema.dump(notifications)


@blueprint.route("/update-notification", methods=["PUT", "DELETE"])
@check_arborist_auth(resource="/services/amanuensis", method="*")
def edit_notification():
    notification_log_id = request.get_json().get("notification_log_id", None)
    message = request.get_json().get("message", None)
    seen = request.get_json().get("seen", None)
    user_id = request.get_json().get("user_id", None)
    expire_date = request.get_json().get("expire_date", None)

    with current_app.db.session as session:

        if not user_id:
            if not notification_log_id and not message:
                raise UserError("A notification ID or a message is required for this endpoint")
            
            notification_log_schema = NotificationLogSchema()

            if request.method == "PUT":
                if not expire_date:
                    raise UserError("An expire date is required for this endpoint")
                try:
                    datetime.strptime(expire_date, "%Y-%m-%d %H:%M:%S.%f")
                except ValueError:
                    raise UserError("A valid datetime is required for this endpoint '%Y-%m-%d %H:%M:%S.%f'")
            
            notification_log_schema = NotificationLogSchema()

            notification = update_notification_log(
                session, 
                id=notification_log_id,
                message=message, 
                expiration_date=expire_date,
                delete=request.method == "DELETE"
            )

            notification = notification_log_schema.dump(notification)

        else:
            if not user_id or not notification_log_id:
                raise UserError("A user id and a notification id is required for this endpoint")

            if seen is None:
                raise UserError("You must pass weather to mark or unmark a notification as seen")
            

            notification_schema = NotificationSchema()
            notification = update_notification(
                session, 
                notification_log_id=notification_log_id, 
                user_id=user_id, 
                seen=seen
            )

            notification = notification_schema.dump(notification)
    
        session.commit()

        return notification

@blueprint.route("/get_users", methods=["GET"])
@check_arborist_auth(resource="/services/amanuensis", method="*")
def fence_get_all_users_info():
    return_value = fence_get_all_users()
    return return_value

@blueprint.route("/project_filter_sets/<project_id>", methods=["GET"])
@check_arborist_auth(resource="/services/amanuensis", method="*")
def get_project_filter_sets(project_id):
    """
    Get all filter sets for a project
    """
    

    search_schema = SearchSchema(many=True)
    project_searches = []
    
    with current_app.db.session as session:
        
        get_projects(session, id=project_id, many=False, throw_not_found=True)

        project_searches = get_project_searches(session, project_id=project_id)
        
        if project_searches:
            project_searches = [project_search.search for project_search in project_searches]
            
        return jsonify(search_schema.dump(project_searches))
  