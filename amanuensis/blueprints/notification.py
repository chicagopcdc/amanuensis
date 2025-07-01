import flask

from amanuensis.auth.auth import current_user
from amanuensis.errors import AuthError
from amanuensis.schema import NotificationSchema
from amanuensis.resources.notification import update_users_notifications, get_all_notifications
from cdislogging import get_logger

logger = get_logger(__name__)

blueprint = flask.Blueprint("notifications", __name__)



@blueprint.route("/", methods=["GET"])
def retrieve_notifications():
    try:
        logged_user_id = current_user.id
    except AuthError:
        logger.warning(
            "Unable to load or find the user, check your token"
        )
    with flask.current_app.db.session as session:
        notification_schema = NotificationSchema(many=True)
        
        messages = update_users_notifications(session, logged_user_id)

        session.commit()
    
        return notification_schema.dump(messages)


blueprint_all = flask.Blueprint("all_notifications", __name__)

@blueprint_all.route("/", methods=["GET"])
def retrive_all_notifications():
    try:
        logged_user_id = current_user.id
    except AuthError:
        logger.warning(
            "Unable to load or find the user, check your token"
        )
        return flask.jsonify({"error": "Unauthorized"}), 401 
    with flask.current_app.db.session as session:
        notification_schema = NotificationSchema(many=True)
        messages = get_all_notifications(session, logged_user_id)
        session.commit()
        return notification_schema.dump(messages)

