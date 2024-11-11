
from amanuensis.resources.userdatamodel.notification import get_notifications, create_notification
from amanuensis.resources.userdatamodel.notification_log import get_notification_logs
from datetime import datetime

def update_users_notifications(session, user_id):
    last_notificaiton_update =  get_notifications(
                                    session, 
                                    user_id=user_id, 
                                    latest=True, 
                                    many=False, 
                                    throw_not_found=False
                                )
    if not last_notificaiton_update:
        latest_notifications = get_notification_logs(session, many=True)
    else:
        latest_notifications = get_notification_logs(session, date_time=last_notificaiton_update.create_date, many=True)


    for notification in latest_notifications:
        create_notification(session, notification_log_id=notification.id, user_id=user_id)
    

    return latest_notifications