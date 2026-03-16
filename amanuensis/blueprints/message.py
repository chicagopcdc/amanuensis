import flask
from amanuensis.auth.auth import current_user
from amanuensis.errors import UserError, AuthNError
from amanuensis.schema import MessageSchema
from amanuensis.resources.message import send_message
from amanuensis.resources.userdatamodel.message import get_messages

from cdislogging import get_logger


blueprint = flask.Blueprint("message", __name__)

logger = get_logger(__name__)


@blueprint.route("/", methods=["GET"])
def get_message():
    try:
        logged_user_id = current_user.id
    except AuthNError:
        raise UserError("Your session has expired. Please log in again to continue.")

    request_id = flask.request.args.get("request_id", None, type=int)

    with flask.current_app.db.session as session:

        message_schema = MessageSchema(many=True)
            
        return message_schema.dump(get_messages(session, logged_user_id, request_id))



@blueprint.route("/", methods=["POST"])
# @debug_log
def create_message():
    """
    Send a message to all the users that are working on a request (requestor plu committee members)

    Returns a json object
    """
    try:
        logged_user_id = current_user.id
    except AuthNError:
        raise UserError("Your session has expired. Please log in again to continue.")
    request_id = flask.request.get_json().get("request_id", None)
    body = flask.request.get_json().get("body", None)
    subject = flask.request.get_json().get("subject", "[PCDC GEN3] Project Activity")

    if not request_id:
        raise UserError("Your request must provide the id of a request to send a message about.")
    
    if not body:
        raise UserError("Your request must provide a body for the message.")

    with flask.current_app.db.session as session:
        message_schema = MessageSchema()

        message = send_message(session, logged_user_id, request_id, subject, body)

        session.commit()
        
        return message_schema.dump(message)



