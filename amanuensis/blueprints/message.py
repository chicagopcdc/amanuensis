import flask

from os import environ
from amanuensis.config import config
from amanuensis.auth.auth import current_user
from amanuensis.errors import AuthError
from amanuensis.schema import MessageSchema
from amanuensis.resources import message as m
from cdislogging import get_logger
from pcdcutils.environment import is_env_enabled


blueprint = flask.Blueprint("message", __name__)

logger = get_logger(__name__)


@blueprint.route("/", methods=["GET"])
def get_messages():
    try:
        logged_user_id = current_user.id
    except AuthError:
        logger.warning(
            "Unable to load or find the user, check your token"
        )

    request_id = flask.request.args.get("request_id", None)

    if request_id:
        request_id = int(request_id)

    if request_id and isinstance(request_id, int):
        msgs = m.get_messages(logged_user_id, request_id)
        message_schema = MessageSchema(many=True)
        return flask.jsonify(message_schema.dump(msgs))
    else:
        msgs = m.get_messages(logged_user_id)
        message_schema = MessageSchema(many=True)
        return flask.jsonify(message_schema.dump(msgs))



@blueprint.route("/", methods=["POST"])
# @debug_log
def send_message():
    """
    Send a message to all the users that are working on a request (requestor plu committee members)

    Returns a json object
    """
    try:
        if is_env_enabled('GEN3_DEBUG'):
            # debug code
            # if we're in debug mode, check if the user_id was sent
            # for testing purposes, otherwise just do normal handling
            logged_user_id = flask.request.get_json().get("user_id", None)
        
        # normal handling
        if not logged_user_id:
            logged_user_id = current_user.id
        
    except AuthError:
        logger.warning(
            "Unable to load or find the user, check your token"
        )

    request_id = flask.request.get_json().get("request_id", None)
    body = flask.request.get_json().get("body", None)
    subject = flask.request.get_json().get("subject", None)

    # subject is optional, use default if not sent with request
    if not subject:
        subject = "[PCDC GEN3] Project Activity"

    logger.debug(f"Message (POST) received: {logged_user_id} {request_id} {subject} {body}")

    # if body is None or body == "":
    #     return 400

    message_schema = MessageSchema()
    return flask.jsonify(message_schema.dump(m.send_message(logged_user_id, request_id, subject, body)))



