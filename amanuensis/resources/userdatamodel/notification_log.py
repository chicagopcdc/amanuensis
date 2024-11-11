from cdislogging import get_logger
from amanuensis.errors import NotFound, UserError
from amanuensis.models import (
    Notification, NotificationLog
)


logger = get_logger(__name__)


def get_notification_logs(current_session, 
                          ids=None, 
                          messages=None, 
                          active=True, 
                          date_time=None,
                          filter_by_active=True, 
                          many=True, 
                          throw_not_found=False):
    logger.info(f"get_notifications: {locals()}")
    
    notification_logs = current_session.query(NotificationLog)

    if filter_by_active:
        notification_logs = notification_logs.filter(NotificationLog.active == active)

    if ids:
        ids = [ids] if not isinstance(ids, list) else ids
        notification_logs = notification_logs.filter(NotificationLog.id.in_(ids))

    if messages:
        messages = [messages] if not isinstance(messages, list) else messages
        notification_logs = notification_logs.filter(NotificationLog.message.in_(messages))

    if date_time:
        notification_logs = notification_logs.filter(NotificationLog.create_date > date_time)

    notification_logs = notification_logs.all()

    if throw_not_found and not notification_logs:
        raise NotFound(f"No notification logs found")

    if not many:
        if len(notification_logs) > 1:
            raise UserError(f"More than one notification log found check inputs")
        else:
            notification_logs = notification_logs[0] if notification_logs else None

    return notification_logs

def update_notification_log(
        session, 
        notification_log=None, 
        id=None, 
        message=None, 
        delete=False
    ):

    if notification_log:
        if not isinstance(notification_log, NotificationLog):
            raise UserError("notification_log must be an instance of NotificationLog")
    
    else:

        notification_log = get_notification_logs(session, ids=id, messages=message, many=False, throw_not_found=True)
    
    notification_log.active = False if delete else notification_log.active

    session.flush()

    return notification_log

def create_notification_log(session, message):
    new_message = get_notification_logs(session, messages=message, filter_by_active=False, many=False)

    if new_message:
        if not new_message.active:
            logger.info(f"Notification log {message} has been reactivated")
            new_message.active = True
        else:
            logger.info(f"Notification log {message} already exists")
    else:
        new_message = NotificationLog(message = message)
        session.add(new_message)
    
    session.flush()
    
    return new_message
