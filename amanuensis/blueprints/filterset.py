import flask
from flask_sqlalchemy_session import current_session

# from amanuensis.auth import login_required, current_token
from amanuensis.resources.filterset import (
    get_all,
    get_by_id,
    create,
    delete,
    update,
    create_snapshot,
    get_snapshot,
)
from amanuensis.config import config
from amanuensis.auth.auth import current_user
from amanuensis.errors import AuthError, UserError
from amanuensis.schema import SearchSchema
from cdislogging import get_logger


logger = get_logger(__name__)

blueprint = flask.Blueprint("filter-sets", __name__)


@blueprint.route("/", methods=["GET"])
# @login_required({"user"})
def get_filter_sets():
    try:
        logged_user_id = current_user.id
    except AuthError:
        logger.warning("Unable to load or find the user, check your token")

    # get the explorer_id from the querystring
    explorer_id = flask.request.args.get("explorerId", default=1, type=int)

    filter_sets = [
        {
            "name": s.name,
            "id": s.id,
            "description": s.description,
            "filters": s.filter_object,
            "ids": s.ids_list,
        }
        for s in get_all(logged_user_id, explorer_id)
    ]
    return flask.jsonify({"filter_sets": filter_sets})


@blueprint.route("/<filter_set_id>", methods=["GET"])
def get_filter_set(filter_set_id):
    try:
        logged_user_id = current_user.id
    except AuthError:
        logger.warning("Unable to load or find the user, check your token")

    # get the explorer_id from the querystring
    explorer_id = flask.request.args.get("explorerId", default=1, type=int)

    filter_sets = [
        {
            "name": s.name,
            "id": s.id,
            "description": s.description,
            "filters": s.filter_object,
            "ids": s.ids_list,
        }
        for s in get_by_id(logged_user_id, filter_set_id, explorer_id)
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

    # search_schema = SearchSchema()
    # return flask.jsonify(search_schema.dump(create(logged_user_id, explorer_id, name, description, filter_object)))

    return flask.jsonify(create(logged_user_id, False, explorer_id, name, description, filter_object, ids_list, graphql_object))


@blueprint.route("/<filter_set_id>", methods=["PUT"])
def update_search(filter_set_id):
    """
    Create a user on the userdatamodel database

    Returns a json object
    """
    try:
        logged_user_id = current_user.id
    except AuthError:
        logger.warning("Unable to load or find the user, check your token")

    # get the explorer_id from the querystring
    explorer_id = flask.request.args.get("explorerId", default=1, type=int)

    name = flask.request.get_json().get("name", None)
    description = flask.request.get_json().get("description", None)
    filter_object = flask.request.get_json().get("filters", None)
    graphql_object = flask.request.get_json().get("gqlFilter", {})
    return flask.jsonify(update(logged_user_id, filter_set_id, explorer_id, name, description, filter_object, graphql_object))


@blueprint.route("/<filter_set_id>", methods=["DELETE"])
def delete_search(filter_set_id):
    """
    Remove the user from the userdatamodel database and all associated storage
    solutions.

    Returns json object
    """
    try:
        logged_user_id = current_user.id
    except AuthError:
        logger.warning("Unable to load or find the user, check your token")

    # get the explorer_id from the querystring
    explorer_id = flask.request.args.get("explorerId", default=1, type=int)

    response = flask.jsonify(delete(logged_user_id, filter_set_id, explorer_id))
    return response


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

    response = flask.jsonify(create_snapshot(logged_user_id, filter_set_id, users_list))
    return response


@blueprint.route("/snapshot/<token>", methods=["GET"])
def get_filter_set_snapshot(token):
    """
    Return the snapshot for the given token.
    """
    try:
        logged_user_id = current_user.id
    except AuthError:
        logger.warning("Unable to load or find the user, check your token")

    response = flask.jsonify(get_snapshot(logged_user_id, token))
    return response
