from amanuensis.resources.userdatamodel.notification import *
import pytest
from amanuensis.models import Notification, NotificationLog
from datetime import datetime, timedelta

################################
# CREATE
# with notification_log id and user id
# block create duplicate
# seen should be false and active should be true

# UPDATE
# Must pass notification or notification_log_id and user_id
# update seen to True
# update active to False
# 
# 
# GET
# filter by user_id
# filter by user_id and notification_log_id
# filter out seen notifications
# filter out delete notifications


################################


@pytest.fixture(scope="session", autouse=True)
def setup_tests(session, register_user):
    user_id, user_email = register_user(email=f"user_1@{__name__}.com", name=__name__)
    user_2_id, user_2_email = register_user(email=f"user_2@{__name__}.com", name=__name__)
    expiration_date = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S.%f")
    not_1 = NotificationLog(message="message user 1", expiration_date=expiration_date)
    not_2 = NotificationLog(message="message user 2", expiration_date=expiration_date)
    not_3 = NotificationLog(message="message 2  user 1", expiration_date=expiration_date)
    not_4 = NotificationLog(message="message user 1 and 2", expiration_date=expiration_date)
    

    session.add_all(
        [
          not_1, not_2, not_3, not_4  
        ]
    )
    session.commit()
    yield user_id, user_2_id, not_1, not_2, not_3, not_4


@pytest.mark.order(1)
def test_create_notification(session, setup_tests):
    user_1_notification = create_notification(session, user_id=setup_tests[0], notification_log_id=setup_tests[2].id)
    user_1_notification_2 = create_notification(session, user_id=setup_tests[0], notification_log_id=setup_tests[4].id)
    session.commit()
    from time import sleep
    sleep(1)
    user_1_notification_3 = create_notification(session, user_id=setup_tests[0], notification_log_id=setup_tests[5].id)

    user_2_notification = create_notification(session, user_id=setup_tests[1], notification_log_id=setup_tests[3].id)
    
    user_2_notification_2 = create_notification(session, user_id=setup_tests[1], notification_log_id=setup_tests[5].id)

    session.commit()

    #get by user id for user 1

    notifications = get_notifications(session, user_id=setup_tests[0], many=True)
    assert len(notifications) == 3

    # get by notification id for user 1
    notifications = get_notifications(session, user_id=setup_tests[0], notification_log_id=setup_tests[5].id)
    assert len(notifications) == 1

    # get by notifications id
    notifications = get_notifications(session, notification_log_id=setup_tests[5].id)
    assert len(notifications) == 2




    #block create duplicate
    user_1_notification_block = create_notification(session, user_id=setup_tests[0], notification_log_id=setup_tests[2].id)
    session.commit()

    

    assert len(session.query(Notification).filter(Notification.notification_log_id == setup_tests[2].id).all()) == 1

@pytest.mark.order(2)
def test_seen_notification(session, setup_tests):
    user_1_notification = update_notification(session, user_id=setup_tests[0], notification_log_id=setup_tests[2].id, seen=True)
    user_1_notification_3 = update_notification(session, user_id=setup_tests[0], notification_log_id=setup_tests[5].id, seen=True)


    session.commit()

    assert user_1_notification.seen == True
    assert user_1_notification_3.seen == True

    # get by user id and seen

    notifications = get_notifications(session, user_id=setup_tests[0], filter_for_seen=True, seen=True, many=True)
    assert len(notifications) == 2

    notifications = get_notifications(session, user_id=setup_tests[0], filter_for_seen=True, seen=False, many=True)
    assert len(notifications) == 1

    # get by notification id and seen

    notifications = get_notifications(session, notification_log_id=setup_tests[5].id, filter_for_seen=True, seen=True, many=True)
    assert len(notifications) == 1

    notifications = get_notifications(session, notification_log_id=setup_tests[5].id, filter_for_seen=True, seen=False, many=True)
    assert len(notifications) == 1

@pytest.mark.order(3)
def test_get_by_create_date(session, setup_tests):

    notifications = get_notifications(session, user_id=setup_tests[0], latest=True, many=False)
    print(notifications)
    assert notifications.notification_log_id == setup_tests[5].id