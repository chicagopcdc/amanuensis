import flask

from os import environ
from amanuensis.config import config
from amanuensis.auth.auth import current_user
from amanuensis.errors import AuthError
from amanuensis.schema import NotificationSchema, NotificationLogSchema
from amanuensis.resources import notification
from cdislogging import get_logger
from pcdcutils.environment import is_env_enabled


blueprint = flask.Blueprint("retriveNotification", __name__)

logger = get_logger(__name__)

@blueprint.route("/", methods=["GET"])
def get_notifications():
    user_notifications = notification.get_notifications()
    notification_schema = NotificationSchema(many=True)
    
    return flask.jsonify(notification_schema.dump(user_notifications))


@blueprint.route("/", methods=["GET"])
def get_all_users():
    user_notifications = notification.get_notifications()
    users = []
    for notif in user_notifications:
        if notif.user_id not in users:
            users.append(notif.user_id)
    
    return users


@blueprint.route("/", methods=["GET"])
def get_unseen_notifications(users):
    get_unseen = notification.get_unseen_notifications(users)
    unseen_schema = NotificationSchema(many=True)
    
    return flask.jsonify(unseen_schema.dump(get_unseen))
