import flask

from amanuensis.auth.auth import current_user
from amanuensis.errors import AuthError
from amanuensis.schema import NotificationSchema, NotificationLogSchema
from amanuensis.resources.notification import update_users_notifications
from amanuensis.resources.userdatamodel.notification import get_notifications
from amanuensis.resources.userdatamodel.notification_log import get_notification_logs
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


@blueprint.route("/all", methods=["GET"])
def retrive_all_notification_log_by_user():
    try:
        logged_user_id = current_user.id
    except AuthError:
        logger.warning(
            "Unable to load or find the user, check your token"
        )
    with flask.current_app.db.session as session:
        notificationlog_schema = NotificationLogSchema(many=True)
        all_notifications = get_notifications(session, user_id = logged_user_id)
        all_notification_logs = get_notification_logs(session, ids=[n.notification_log_id for n in all_notifications] , expired=False)
        return notificationlog_schema.dump(all_notification_logs)