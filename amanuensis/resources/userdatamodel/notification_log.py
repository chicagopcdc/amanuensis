from cdislogging import get_logger
from amanuensis.errors import NotFound, UserError
from amanuensis.models import (
    Notification, NotificationLog
)
from datetime import datetime

logger = get_logger(__name__)


def get_notification_logs(current_session, 
                          ids=None, 
                          messages=None, 
                          active=True, 
                          date_time=None,
                          expired=True,
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

    if expired:
        notification_logs = notification_logs.filter(NotificationLog.expiration_date > datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))

    notification_logs = notification_logs.all()

    if throw_not_found and not notification_logs:
        raise NotFound(f"No notification logs found")

    if not many:
        if len(notification_logs) > 1:
            raise UserError("More than one notification log found check inputs")
        else:
            notification_logs = notification_logs[0] if notification_logs else None

    return notification_logs

def update_notification_log(
        session, 
        notification_log=None, 
        id=None, 
        message=None,
        expiration_date=None, 
        delete=False
    ):

    if notification_log:
        if not isinstance(notification_log, NotificationLog):
            raise UserError("notification_log must be an instance of NotificationLog")
    
    else:
        notification_log = get_notification_logs(session, ids=id, messages=message, expired=False, many=False, throw_not_found=True)
    
    notification_log.active = False if delete else notification_log.active

    if expiration_date is not None:
        expiration_date = datetime.strptime(expiration_date, "%Y-%m-%d %H:%M:%S.%f")
        notification_log.expiration_date = expiration_date

    session.flush()

    return notification_log

def create_notification_log(session, message, expiration_date):
    new_message = get_notification_logs(session, messages=message, expired=False, filter_by_active=False, many=False)
    expiration_date = datetime.strptime(expiration_date, "%Y-%m-%d %H:%M:%S.%f")
    if new_message:
        if not new_message.active:
            logger.info(f"Notification log {message} has been reactivated")
            new_message.active = True
            new_message.expiration_date = expiration_date
        else:
            logger.info(f"Notification log {message} already exists")
    else:

        new_message = NotificationLog(message = message, expiration_date = expiration_date)
        session.add(new_message)
    
    session.flush()
    
    return new_message
