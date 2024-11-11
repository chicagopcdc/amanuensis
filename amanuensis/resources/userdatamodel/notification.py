from flask import current_app
from sqlalchemy import func
from cdislogging import get_logger
from amanuensis.errors import NotFound, UserError
from amanuensis.models import (
    Notification, NotificationLog
)

logger = get_logger(__name__)


def get_notifications(session, 
                      user_id=None, 
                      notification_log_id=None, 
                      seen=False,
                      latest=False, 
                      filter_for_seen=False, 
                      many=True, 
                      throw_not_found=False):
    
    notifications = session.query(Notification)

    if user_id:
        notifications = notifications.filter(Notification.user_id == user_id)

    if notification_log_id:
        notifications = notifications.filter(Notification.notification_log_id == notification_log_id)

    if filter_for_seen:
        notifications = notifications.filter(Notification.seen == seen)

    if latest:
        notifications = notifications.order_by(Notification.create_date.desc()).first()
        notifications = [notifications] if notifications else []
    else:
        notifications = notifications.all()

    if throw_not_found and not notifications:
        raise NotFound(f"No notifications found")

    if not many:
        if len(notifications) > 1:
            raise UserError(f"More than one notification found check inputs")
        else:
            notifications = notifications[0] if notifications else None

    return notifications

def create_notification(session, notification_log_id, user_id):

    notification = get_notifications(session, user_id=user_id, notification_log_id=notification_log_id, many=False)

    if notification:
        logger.info(f"Notification {notification.messages.message} already exists for user {user_id}")
    else:

        notification = Notification(notification_log_id=notification_log_id, user_id=user_id)

        
        session.add(notification)
    
    session.flush()

    return notification


def update_notification(session, notification=None, user_id=None, notification_log_id=None, seen=None):
    
    if notification:
        if not isinstance(notification, Notification):
            raise UserError("notification must be an instance of Notification")
    
    else:

        notification = get_notifications(session, user_id=user_id, notification_log_id=notification_log_id, many=False, throw_not_found=True)
    
    if seen is not None:
        notification.seen = seen

    session.flush()

    return notification















# Change notification status
def change_seen_status(current_session, notifications):
    current_session.bulk_save_objects(notifications)
    current_session.commit()
    return new_notications








