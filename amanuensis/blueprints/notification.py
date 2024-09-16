import flask

from os import environ
from amanuensis.config import config
from amanuensis.auth.auth import current_user
from amanuensis.errors import AuthError
from amanuensis.schema import NotificationSchema
from amanuensis.resources import notification
from cdislogging import get_logger
from pcdcutils.environment import is_env_enabled


blueprint = flask.Blueprint("retriveNotification", __name__)

logger = get_logger(__name__)

@blueprint.route("/", methods=["GET"])
def retrieve_unseen():
    try:
        logged_user_id = current_user.id
    except AuthError:
        logger.warning(
            "Unable to load or find the user, check your token"
        )
    notification_schema = NotificationSchema(many=True)
    unseen = notification.get_unseen_notifications(logged_user_id)

    return flask.jsonify(notification_schema.dump(unseen))


@blueprint.route("/", methods=["POST"])
def inject_new():
    try:
        logged_user_id = current_user.id
    except AuthError:
        logger.warning(
            "Unable to load or find the user, check your token"
        )
        
    notification_schema = NotificationSchema(many=True)
    user_notifications = notification.inject_user(logger)
    
    return flask.jsonify(notification_schema.dump(user_notifications))

