import flask
import json
from cdislogging import get_logger
from pcdcutils.environment import is_env_enabled
from amanuensis.config import config
from amanuensis.errors import NotFound, Unauthorized, UserError, InternalError, Forbidden

from amanuensis.resources.userdatamodel import userdatamodel_notifcation
from userdatamodel_notifcation import (
    delete_notification_log,
    change_seen_status,
    get_all_notification_by_user,
    get_all_notifications,
    create_new_notification, 
)

from amanuensis.models import (
    Notification, 
    NotifcationLog
)

from amanuensis.schema import NotificationSchema, NotificationLogSchema

logger = get_logger(__name__)


# Create a notification log and notifications to go with a user
def create_notification(message):
    with flask.current_app.db.session as session:
        notification_schema = NotificationLogSchema()
        new_message = create_new_notification(session, message)
        notification_schema.dump(new_message)
        return new_message


# Get all notifications in the db
def get_notifications():
    with flask.current_app.db.session as session:
        notification_schema = NotificationLogSchema(many=True)
        notifications = get_all_notifications(session)
        notification_schema.dump(notifications)
        return notifications


# Get the notifications that are not seen
def get_unseen_notifications(user_id):
    unseen = []
    # Get all notifications
    all_notifications = get_notifications()

    with flask.current_app.db.session as session:
        notification_schema = NotificationLogSchema(many=True)
        # Get seen notificaitons
        seen = get_all_notification_by_user(session, user_id)
        seen_notification_ids = [obj.notification_id for obj in seen]

        # All minus seen
        unseen = [notification for notification in all_notifications if notification.id not in seen_notification_ids]
        

        # TODO set the unseen in the DB as seen CHANGE
        # This should be a new API endpoint that the FE calls after actually displaying the messages and potentially changing the status after the user clicks on them
        new_seen = []
        for notification in unseen:
            new_seen.append(Notification(notification_id=notification.id, 
                                            user_id=user_id))
        change_seen_status(session, new_seen)
        # END TODO CHANGE

        notification_schema.dump(unseen)
        return unseen

def get_seen_notifications_by(user_id=None, notification_id=None):
    if user_id:
        with flask.current_app.db.session as session:
            return get_all_notification_by_user(session, user_id)
    if notification_id:
        return get_user_by_notification(notification_id)


def get_user_by_notification(notification_id):
    with flask.current_app.db.session as session:

def delete_notification(notification_id):
    with flask.current_app.db.session as session:
        delete_notification_log(session, notification_id)
        return


     




