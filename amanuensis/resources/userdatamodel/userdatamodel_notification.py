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
    "get_all_notification",
    "get_all_notiflogs",
    "get_notifications_by_user",
    "get_log_associated",
    "get_notification_by_log",
    "check_seen"
    "check_unseen_notifications",
    "create_new_notification",
    "change_seen_status",
    "delete_object"
]

# Get all notifications in the DB
def get_all_notifications(current_session):
    notifications = current_session.query(Notification)
    return notifications


def get_all_notiflogs(current_session):
    logs = current_session.query(NotificationLog)
    return logs


# Get all notifications associated with a user
def get_notifications_by_user(current_session, logged_user_id):
    notifications = current_session.query(Notification).filter_by(user_id = logged_user_id)
    return notifications


# Get all notifications associated with a log
def get_log_assoiciated(current_session, log_id):
    notifications = current_session.query(Notification).filter_by(notification_id = log_id)
    return notifications


# Get notification log
def get_notification_by_log(current_session, notification_id):
    log = current_session.query(NotificationLog).filter_by(id = notification_id).all()
    return log


# Check if a notification is seen, fix last login check
def check_seen(notification_log, user):
    last_login = user.update_date
    notif_create = notification_log.create_date
    return last_login >= notif_create


# Check all of the unseen notifications
def check_unseen_notifications(current_session, logged_user_id):
    notifications = get_all_notifications(current_session,logged_user_id)
    unseen_notifications = []

    # for all notifications get log and user
    for notification in notifications:
        notif_id = notification.notification_id
        log = get_notification_by_log(current_session, notif_id)
        user = notification.user_id

        # if log not already added as unseen add it
        if not check_seen(log, user):
            if log not in unseen_notifications:
                unseen_notifications.append(get_notification_by_log(current_session, notif_id))

    return unseen_notifications


# Create new notification and create notifications associated with all users
def create_new_notification(current_session, user_ids, message):
    notif_log = NotificationLog(notif_message = message)
    notif_id = notif_log.id

    user_associated_notifcations = []
    for user in user_ids:
        associated_notif = Notification(notification_id = notif_id, user_id = user)
        user_associated_notifcations.append(associated_notif)

    return (notif_log, user_associated_notifcations)


# Change notification status
def change_seen_status(current_session, notification):
    new_notication = Notification(notification_id = notification.notifcation_id, user_id = notification.user_id, seen = True) 
    return new_notication


def delete_object(current_session, notification = None, log = None): 
    # if given a notification delete it, if given a log delete it 
    if notification:
        current_session.query(Notification).filter(user_id = notification.user_id, notification_id = notification.notification_id).delete()
        current_session.commit()

    if log:
        current_session.query(Notification).filter(notification_id = notification.notification_id).delete()
        current_session.query(NotificationLog).filter(id = log.id).delete()
        current_session.commit
