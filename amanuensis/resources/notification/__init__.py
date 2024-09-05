import flask
import json
from cdislogging import get_logger
from pcdcutils.environment import is_env_enabled
from amanuensis.config import config
from amanuensis.errors import NotFound, Unauthorized, UserError, InternalError, Forbidden

from amanuensis.resources.userdatamodel import userdatamodel_notifcation
from userdatamodel_notifcation import (
    get_all_notifications, 
    get_all_notiflogs,
    get_notifications_by_user,
    get_log_associated,
    get_notification_by_log, 
    check_seen, 
    check_unseen_notifications,
    delete_object, 
    create_new_notification, 
    change_seen_status
)

from amanuensis.auth.auth import current_user
from amanuensis.models import (
    Notification, 
    NotifcationLog
)

from amanuensis.schema import NotificationSchema, NotificationLogSchema

logger = get_logger(__name__)

# Get all notifications in the db
def get_notifications():
    with flask.current_app.db.session as session:
        notifications = get_all_notifications(session)
        return notifications


def get_notif_logs():
    with flask.current_app.db.session as session:
        notiflogs = get_all_notiflogs(session)
        return notiflogs  


# If log id is given give log info else give user associated info
def get_notification_info(user_id = None, log_id = None):
    with flask.current_app.db.session as session:
        if log_id is not None:
            notification_log = get_notification_by_log(session, log_id)
            return notification_log

        if user_id is not None:
            notifications = get_notifications_by_user(session, user_id)
            return notifications


# Create a notification log and notifications to go with a user
def create_notification(messages, user_ids):
    notification_schema = NotificationSchema(many = True)
    notificationlog_schema = NotificationLogSchema(many = True)
    new_logs = []
    with flask.current_app.db.session as session:
        for message in messages:
            new_notifLog, new_notif_for_users = create_new_notification(session, user_ids, message)
            notificationlog_schema.dump(new_notifLog)
            notification_schema.dump(new_notif_for_users)
            new_logs.append(new_notifLog)

        return new_logs


# If a notification has been see update it then delete the old notification. If all notifications seen delete log
def update_notifications():
    logs = get_notif_logs()
    notification_schema = NotificationSchema(many = True)
    seen_valid = True

    with flask.current_app.db.session as session:
        for log in logs:
            notifications = get_log_associated(session)
            new_notifications = []

            for notification in notifications:
                if check_seen(log, notification.user_id):
                    new_notifications.append(change_seen_status(session, notification))
                    delete_object(session, notification = notification)
                    continue

                seen_valid = False

            if seen_valid:
                delete_object(session, log = log)
            else:
                notification_schema.dump(new_notifications)
            

# Get the notifications that are not seen
def get_unseen_notifications(users):
    unseen = []
    with flask.current_app.db.session as session:
        update_notifications()
        for user in users:
            user_unseen = check_unseen_notifications(session, user)
            unseen.extend(user_unseen)

        return unseen
