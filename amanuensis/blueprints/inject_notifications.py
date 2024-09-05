import flask

from os import environ
from amanuensis.config import config
from amanuensis.auth.auth import current_user
from amanuensis.errors import AuthError
from amanuensis.schema import NotificationSchema, NotificationLogSchema
from amanuensis.resources import notification
from cdislogging import get_logger
from pcdcutils.environment import is_env_enabled

blueprint = flask.Blueprint("injectNotification", __name__)

logger = get_logger(__name__)


@blueprint.route("/", methods=["GET"])
def get_all_users():
    user_notifications = notification.get_notifications()
    users = []
    for notif in user_notifications:
        if notif.user_id not in users:
            users.append(notif.user_id)
    
    return users


@blueprint.route("/", methods=["POST"])
def add_notifications(messages, user_ids):
    try:
        logged_user_id = current_user.id
    except AuthError:
        logger.warning(
            "Unable to load or find the user, check your token"
        )

    new_logs = notification.create_notification(messages, user_ids)
    log_schema = NotificationLogSchema(many=True)

    return flask.jsonify(log_schema.dump(new_logs))
