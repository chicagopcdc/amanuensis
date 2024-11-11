import pytest
from amanuensis.models import NotificationLog, Notification
from amanuensis.resources.userdatamodel.notification_log import *
from datetime import datetime
from time import sleep

@pytest.mark.order(1)
def test_create_notification_log(session):

    message = f"{__name__} test message"
    notification_log = create_notification_log(session, message)
    session.commit()
    assert notification_log
    message_from_db = session.query(NotificationLog).filter(NotificationLog.id == notification_log.id).all()

    assert len(message_from_db) == 1
    notification = message_from_db[0]
    assert notification.message == notification_log.message
    assert notification.create_date == notification_log.create_date
    assert True == notification_log.active


    #block create duplicate
    create_notification_log(session, message)
    assert len(session.query(NotificationLog).filter(NotificationLog.message == message).all()) == 1

@pytest.mark.order(2)
def test_delete_and_reactivate_notification_log(session):
     message = f"{__name__} test delete and reactivate"

     notification_log = create_notification_log(session, message)
     assert notification_log
     session.commit()
     

     #TEST DELETE
     update_notification_log(session, id=notification_log.id, delete=True)

     with pytest.raises(NotFound):    
        get_notification_logs(session, ids=notification_log.id, many=False, throw_not_found=True)

     #TEST REACTIVATE
     create_notification_log(session, message)
     session.commit()

     reactivate_message = get_notification_logs(session, ids=notification_log.id, many=False, throw_not_found=True)
     
     assert reactivate_message.id == notification_log.id

     reactivate_message.active = True



@pytest.mark.order(3)
def test_get_notification_logs(session):
    
    get_by_notfi_message = get_notification_logs(session, messages=f"{__name__} test message", many=False)

    assert get_by_notfi_message

    get_by_id = get_notification_logs(session, ids=get_by_notfi_message.id, many=False)

    assert get_by_id

    assert get_by_id.id == get_by_notfi_message.id

    get_by_ids = get_notification_logs(session, messages=[f"{__name__} test message", f"{__name__} test delete and reactivate"], many=True)

    assert len(get_by_ids) == 2

    session.commit()


    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    print(time_now)

    sleep(1)

    create_notification_log(session, f"{__name__} test filter by date time")

    session.commit()

    assert len(get_notification_logs(session, date_time=time_now, many=True)) == 1



