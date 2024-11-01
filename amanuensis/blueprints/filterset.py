import flask
from amanuensis.resources.userdatamodel.search import get_filter_sets, create_filter_set, update_filter_set
from amanuensis.resources.userdatamodel.search_is_shared import get_shared_filter_sets, create_filter_set_snapshot
from amanuensis.auth.auth import current_user
from amanuensis.errors import AuthError, UserError
from cdislogging import get_logger
from amanuensis.schema import SearchSchema, SearchIsSharedSchema


logger = get_logger(__name__)

blueprint = flask.Blueprint("filter-sets", __name__)



@blueprint.route("/", methods=["GET"])
@blueprint.route("/<filter_set_id>", methods=["GET"])
def get_filter_set(filter_set_id=None):
    try:
        logged_user_id = current_user.id
    except AuthError:
        logger.warning("Unable to load or find the user, check your token")

    # get the explorer_id from the querystring
    explorer_id = flask.request.args.get("explorerId", default=1, type=int)

    with flask.current_app.db.session as session:
        filter_sets = [
            {
                "name": s.name,
                "id": s.id,
                "description": s.description,
                "filters": s.filter_object,
                "ids": s.ids_list,
            }
            for s in get_filter_sets(session, explorer_id=explorer_id, id=filter_set_id, user_id=logged_user_id)
        ]
        return flask.jsonify({"filter_sets": filter_sets})


@blueprint.route("/", methods=["POST"])
def create_search():
    """
    Create a search on the userportaldatamodel database

    Returns a json object
    """
    try:
        logged_user_id = current_user.id
    except AuthError:
        logger.warning("Unable to load or find the user, check your token")

    # get the explorer_id from the querystring
    explorer_id = flask.request.args.get("explorerId", default=1, type=int)
    name = flask.request.get_json().get("name", None)
    filter_object = flask.request.get_json().get("filters", {})
    graphql_object = flask.request.get_json().get("gqlFilter", {})
    description = flask.request.get_json().get("description", None)
    ids_list = flask.request.get_json().get("ids_list", None)

    with flask.current_app.db.session as session:
        new_filter_set = create_filter_set(
            session,
            logged_user_id=logged_user_id,
            is_amanuensis_admin=False, 
            explorer_id=explorer_id, 
            name=name, 
            description=description, 
            filter_object=filter_object, 
            ids_list=ids_list, 
            graphql_object=graphql_object
        )
        session.commit()
        return flask.jsonify({
            "name": new_filter_set.name, 
            "id": new_filter_set.id,
            "explorer_id": new_filter_set.filter_source_internal_id,
            "description": new_filter_set.description, 
            "filters": new_filter_set.filter_object
        })


@blueprint.route("/<filter_set_id>", methods=["PUT", "DELETE"])
def update_search(filter_set_id):
    """
    Update a search on the userportaldatamodel database

    Returns a json object
    """
    try:
        logged_user_id = current_user.id
    except AuthError:
        logger.warning("Unable to load or find the user, check your token")

    # get the explorer_id from the querystring
    explorer_id = flask.request.args.get("explorerId", default=1, type=int)
    
    if flask.request.method == "PUT":
        name = flask.request.get_json().get("name", None)
        description = flask.request.get_json().get("description", None)
        filter_object = flask.request.get_json().get("filters", None)
        graphql_object = flask.request.get_json().get("gqlFilter", {})
    
    else:
        name = None 
        description = None
        filter_object = None
        graphql_object = {}


    search_schema = SearchSchema()

    with flask.current_app.db.session as session:
        
        updated_filter_set = update_filter_set(
                                    session, 
                                    logged_user_id, 
                                    filter_set_id, 
                                    explorer_id, 
                                    name=name, 
                                    description=description, 
                                    filter_object=filter_object, 
                                    graphql_object=graphql_object,
                                    delete= True if flask.request.method == "DELETE" else False
                                )
    
        return search_schema.dump(updated_filter_set)


@blueprint.route("/snapshot", methods=["POST"])
def create_snapshot_from_filter_set():
    """
    Create a snapshot of a filter set given its id.

    Returns the snapshot if successful.
    """
    try:
        logged_user_id = current_user.id
    except AuthError:
        logger.warning("Unable to load or find the user, check your token")

    filter_set_id = flask.request.get_json().get("filterSetId", None) #"filter_set_id", default=None, type=int
    users_list = flask.request.get_json().get("users_list", None)
    if not filter_set_id:
        raise UserError("Missing parameters.")
    
    
    with flask.current_app.db.session as session:
        snapshot = create_filter_set_snapshot(session, logged_user_id, filter_set_id, users_list)

        return flask.jsonify(snapshot)


@blueprint.route("/snapshot/<token>", methods=["GET"])
def get_filter_set_snapshot(token):
    """
    Return the snapshot for the given token.
    """
    try:
        current_user.id
    except AuthError:
        logger.warning("Unable to load or find the user, check your token")
    
    with flask.current_app.db.session as session:
        snapshot = get_shared_filter_sets(session, token)

    return flask.jsonify(snapshot)







