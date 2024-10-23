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

__all__ = [
    "create_new_notification",
    "get_all_notifications",
    "get_all_notification_by_user",
    "change_seen_status",
    "delete_notification_log",
    "get_user_by_notification"
]


# Create new notification and create notifications associated with all users
def create_new_notification(current_session, message):
    new_message = NotificationLog(notif_message = message)
    current_session.add(new_message)
    current_session.commit()
    return new_message


# Get all notifications in the DB
def get_all_notifications(current_session):
    notifications = current_session.query(NotificationLog).all()
    return notifications


# Get notification log
def get_all_notification_by_user(current_session, user_id):
    logs = current_session.query(Notification)
                            .filter_by(user_id = user_id)
                            .all()
    return logs

def get_user_by_notification(current_session, notification_id):
    logs = current_session.query(Notification)
                            .filter_by(notification_id = notification_id)
                            .all()
    return logs

# Change notification status
def change_seen_status(current_session, notifications):
    current_session.bulk_save_objects(notifications)
    current_session.commit()
    return new_notications


def delete_notification_log(current_session, notification_id): 
    current_session.query(Notification)
                    .filter(notification_id = notification_id)
                    .delete()
    current_session.query(NotificationLog)
                    .filter(id = notification_id)
                    .delete()
    current_session.commit()







