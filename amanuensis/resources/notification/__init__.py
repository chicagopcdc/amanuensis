import flask
import json
from cdislogging import get_logger
from pcdcutils.environment import is_env_enabled
from amanuensis.config import config
from amanuensis.errors import NotFound, Unauthorized, UserError, InternalError, Forbidden

from amanuensis.resources.userdatamodel import userdatamodel_notifcation
from userdatamodel_notifcation import (
    get_all_notifications, 
    get_all_logs,
    get_log_unseen,
    get_user_unseen,
    change_seen_status,
    delete_object, 
    create_new_notification, 
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


# If log id is given give log info else give user associated info
def get_notification_info(user_id = None, log_id = None):
    with flask.current_app.db.session as session:
        if log_id is not None:
            notifications = get_log_unseen(session, log_id)
            return notifications

        if user_id is not None:
            notifications = get_user_unseen(session, user_id)
            return notifications


# Create a notification log and notifications to go with a user
def create_notification(message):
    notification_log_schema = NotificationLogSchema(many = True)

    with flask.current_app.db.session as session:
        new_log = create_new_notification(message)
        notification_log_schema.dump(new_log)

        return new_log
    

def inject_user(user):
    with flask.current_app.db.session as session:
        logs = get_all_logs(session)
        notifications = []

        for log in logs:
            new_notification = Notification(notification_id = log.id, user_id = user, seen = False)
            notifications.append(new_notification)

        return notifications 


# Instead check if all logs are seen to delete a log
def update_notifications(log_id):
    with flask.current_app.db.session as session:
        unseen_logs = get_log_unseen(session, log_id)

        if unseen_logs is None:
            delete_object(session, log = log_id)         


# Get the notifications that are not seen
def get_unseen_notifications(user):
    unseen = []
    with flask.current_app.db.session as session:
        notifications = get_user_unseen(session, user)
        updated_seen = []
        
        for notification in notifications:
            updated = change_seen_status(notification)
            delete_object(notification)
            updated_seen.append(updated)

        return updated_seen

