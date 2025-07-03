import flask

from amanuensis.auth.auth import current_user
from amanuensis.errors import AuthError
from amanuensis.schema import NotificationSchema, NotificationLogSchema
from amanuensis.resources.notification import update_users_notifications
from cdislogging import get_logger
from amanuensis.models import Notification, NotificationLog

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
def retrive_all_notification_log():
    try:
        logged_user_id = current_user.id
    except AuthError:
        logger.warning(
            "Unable to load or find the user, check your token"
        )
    with flask.current_app.db.session as session:
        notifications_with_logs = (
            session.query(Notification, NotificationLog)
            .join(NotificationLog, Notification.notification_log_id == NotificationLog.id)
            .filter(Notification.user_id == logged_user_id)
            .order_by(Notification.create_date.desc())
            .all()
        )
        notification_logs = []
        for notification, log in notifications_with_logs:
          notification_logs.append(
              {
              "notification_id":notification.id,
              "user_id":notification.user_id,
              "seen":notification.seen,
              "date":notification.create_date.isoformat() if log.create_date else 'N/A',
              "message":log.message,
              "expiration_date":log.expiration_date.isoformat() if log.expiration_date else 'N/A'
              }
          )
        return flask.jsonify(notification_logs)