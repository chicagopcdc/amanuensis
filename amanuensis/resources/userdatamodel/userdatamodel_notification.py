from flask import current_app
from sqlalchemy import func
from cdislogging import get_logger
from amanuensis.errors import NotFound, UserError
from amanuensis.models import (
    Notification, NotificationLog
)

# do this until AWS-related requests is handled by it's own project
from pcdcutils.environment import is_env_enabled

logger = get_logger(__name__)

#########updateeeeee
__all__ = [
    "get_all_notification",
    "get_log_associated",
    "get_notification_by_log",
    "get_user_unseen",
    "change_seen_status",
    "create_new_notification",
    "delete_object"
]

# Get all notifications in the DB
def get_all_notifications(current_session):
    notifications = current_session.query(Notification).all()
    return notifications

# Get notification log
def get_all_logs(current_session, notification_id):
    logs = current_session.query(NotificationLog).all()
    return logs

# Get all notifications associated with a log
def get_log_unseen(current_session, log_id):
    notifications = current_session.query(Notification).filter_by(notification_id = log_id, seen = False)
    return notifications

# Get all notifications associated with a user
def get_user_unseen(current_session, logged_user_id):
    notifications = current_session.query(Notification).filter_by(user_id = logged_user_id, seen = False)
    return notifications 

# Change notification status
def change_seen_status(notification):
    new_notication = Notification(notification_id = notification.notifcation_id, user_id = notification.user_id, seen = True) 
    return new_notication


# Create new notification and create notifications associated with all users
def create_new_notification(current_session, message):
    new_log = NotificationLog(notif_message = message)
    return new_log


def delete_object(current_session, notification = None, log = None): 
    # if given a notification delete it, if given a log delete it 
    if notification:
        current_session.query(Notification).filter(user_id = notification.user_id, notification_id = notification.notification_id).delete()
        current_session.commit()

    if log:
        current_session.query(Notification).filter(notification_id = notification.notification_id).delete()
        current_session.query(NotificationLog).filter(id = log.id).delete()
        current_session.commit
