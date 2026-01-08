import pytest
from amanuensis.resources.userdatamodel.associated_users import get_associated_users, update_associated_user, create_associated_user
from amanuensis.errors import NotFound, InternalError, UserError
from amanuensis.models import AssociatedUser
from unittest.mock import MagicMock, patch

def test_create_associated_user_exists_in_fence(session, register_user):
    #test create user with email and user_id
    email_1 = f"user_1@{__name__}.com"
    user_id, user_email = register_user(email=email_1, name=__name__)
    new_user = create_associated_user(session, email=email_1, user_id=user_id)
    session.commit()
    user_in_db = session.query(AssociatedUser).filter_by(email=email_1).all()
    assert len(user_in_db) == 1
    assert user_in_db[0].email == email_1
    assert user_in_db[0].user_id == user_id
    assert user_in_db[0].user_source == "fence"
    assert user_in_db[0].active == True
    assert user_in_db[0].id == new_user.id
    assert user_in_db[0].create_date is not None
    assert user_in_db[0].update_date is not None
    assert user_in_db[0].projects == []
    assert user_in_db[0].project_has_associated_user == []

def test_create_associated_user_exists_in_other_source(session, register_user):
    #test create user with email and user_id
    email_2 = f"user_2@{__name__}.com"
    user_id, user_email = register_user(email=email_2, name=__name__)
    new_user = create_associated_user(session, email=email_2, user_id=user_id, user_source="chicago")
    session.commit()
    user_in_db = session.query(AssociatedUser).filter_by(email=email_2).all()
    assert len(user_in_db) == 1
    assert user_in_db[0].email == email_2
    assert user_in_db[0].user_id == user_id
    assert user_in_db[0].user_source == "chicago"
    assert user_in_db[0].active == True
    assert user_in_db[0].id == new_user.id
    assert user_in_db[0].create_date is not None
    assert user_in_db[0].update_date is not None
    assert user_in_db[0].projects == []
    assert user_in_db[0].project_has_associated_user == []

def test_create_associated_user_not_signed_up(session):
    #test create user with email only
    email_3 = f"user_3@{__name__}.com"
    new_user = create_associated_user(session, email=email_3)
    session.commit()
    user_in_db = session.query(AssociatedUser).filter_by(email=email_3).all()
    assert len(user_in_db) == 1
    assert user_in_db[0].email == email_3
    assert user_in_db[0].user_id is None
    assert user_in_db[0].user_source is None
    assert user_in_db[0].active == False
    assert user_in_db[0].id == new_user.id
    assert user_in_db[0].create_date is not None
    assert user_in_db[0].update_date is not None
    assert user_in_db[0].projects == []
    assert user_in_db[0].project_has_associated_user == []

def test_dont_recreate_active_associated_user(session, register_user):
    #create active user
    email_5 = f"user_5@{__name__}.com"
    user_id, user_email = register_user(email=email_5, name=__name__)
    new_user = create_associated_user(session, email=email_5, user_id=user_id)
    session.commit()
    user_in_db = session.query(AssociatedUser).filter_by(email=email_5).all()
    assert len(user_in_db) == 1
    assert user_in_db[0].active == True
    #try to recreate active user
    recreated_user = create_associated_user(session, email=email_5, user_id=user_id)
    session.commit()
    user_in_db = session.query(AssociatedUser).filter_by(email=email_5).all()
    assert len(user_in_db) == 1
    assert user_in_db[0].active == True
    assert user_in_db[0].id == recreated_user.id
    assert user_in_db[0].id == new_user.id

def test_dont_activate_user_who_never_signed_up(session):
    #create inactive user
    email_6 = f"user_6@{__name__}.com"
    new_user = create_associated_user(session, email=email_6)
    session.commit()
    user_in_db = session.query(AssociatedUser).filter_by(email=email_6).all()
    assert len(user_in_db) == 1
    assert user_in_db[0].active == False
    #try to recreate inactive user
    recreated_user = create_associated_user(session, email=email_6)
    session.commit()
    user_in_db = session.query(AssociatedUser).filter_by(email=email_6).all()
    assert len(user_in_db) == 1
    assert user_in_db[0].active == False
    assert user_in_db[0].id == recreated_user.id
    assert user_in_db[0].id == new_user.id

def test_reactivate_associated_user(session, register_user):
    #create inactive user
    email_4 = f"user_4@{__name__}.com"
    user_id, user_email = register_user(email=email_4, name=__name__)
    new_user = create_associated_user(session, email=email_4, user_id=user_id)
    session.commit()
    #deactivate user
    update_associated_user(session, new_user, delete=True)
    session.commit()
    user_in_db = session.query(AssociatedUser).filter_by(email=email_4).all()
    assert len(user_in_db) == 1
    assert user_in_db[0].active == False
    assert user_in_db[0].id == new_user.id
    #reactivate user
    reactivated_user = create_associated_user(session, email=email_4, user_id=user_id)
    session.commit()
    user_in_db = session.query(AssociatedUser).filter_by(email=email_4).all()
    assert len(user_in_db) == 1
    assert user_in_db[0].active == True
    assert user_in_db[0].id == new_user.id  

def test_delete_associated_user(session, register_user):
    #create active user
    email_7 = f"user_7@{__name__}.com"
    user_id, user_email = register_user(email=email_7, name=__name__)
    new_user = create_associated_user(session, email=email_7, user_id=user_id)
    session.commit()
    user_in_db = session.query(AssociatedUser).filter_by(email=email_7).all()
    assert len(user_in_db) == 1
    assert user_in_db[0].active == True
    assert user_in_db[0].id == new_user.id
    #delete user
    deleted_user = update_associated_user(session, new_user, delete=True)
    session.commit()        
    user_in_db = session.query(AssociatedUser).filter_by(email=email_7).all()
    assert len(user_in_db) == 1
    assert user_in_db[0].active == False
    assert user_in_db[0].id == new_user.id

def test_ignore_update_associated_user_who_hasnt_signed_up(session, register_user):
    #create active user
    email_8 = f"user_8@{__name__}.com"
    new_user = create_associated_user(session, email=email_8)
    session.commit()
    user_in_db = session.query(AssociatedUser).filter_by(email=email_8).all()
    assert len(user_in_db) == 1
    assert user_in_db[0].active == False
    assert user_in_db[0].id == new_user.id

    #update user_source but nothing happens cause no user_id
    updated_user = update_associated_user(session, old_email=email_8, new_user_source="chicago")
    session.commit()        
    user_in_db = session.query(AssociatedUser).filter_by(email=email_8).all()
    assert len(user_in_db) == 1
    assert user_in_db[0].active == False
    assert user_in_db[0].user_source is None
    assert user_in_db[0].user_id is None
    assert user_in_db[0].id == new_user.id

def test_update_email_of_user_not_signed_up(session, register_user):
    #update email of user who has not signed up
    email_9 = f"user_9@{__name__}.com"
    new_user = create_associated_user(session, email=email_9)
    session.commit()
    user_in_db = session.query(AssociatedUser).filter_by(email=email_9).all()
    assert len(user_in_db) == 1
    assert user_in_db[0].active == False
    assert user_in_db[0].id == new_user.id

    new_email = f"user_9_updated@{__name__}.com"
    updated_user = update_associated_user(session, old_email=email_9, new_email=new_email)
    session.commit()        
    user_in_db = session.query(AssociatedUser).filter_by(email=new_email).all()
    assert len(user_in_db) == 1
    assert user_in_db[0].active == False
    assert user_in_db[0].email == new_email
    assert user_in_db[0].id == new_user.id

def test_update_user_id_of_user_not_signed_up(session, register_user):
    #update user_id of user who has not signed up
    email_10 = f"user_10@{__name__}.com"
    new_user = create_associated_user(session, email=email_10)
    session.commit()
    user_in_db = session.query(AssociatedUser).filter_by(email=email_10).all()
    assert len(user_in_db) == 1
    assert user_in_db[0].active == False
    assert user_in_db[0].id == new_user.id

    user_id, user_email = register_user(email=email_10, name=__name__)
    updated_user = update_associated_user(session, old_email=email_10, new_user_id=user_id)
    session.commit()        
    user_in_db = session.query(AssociatedUser).filter_by(email=email_10).all()
    assert len(user_in_db) == 1
    assert user_in_db[0].active == True
    assert user_in_db[0].user_id == user_id
    assert user_in_db[0].id == new_user.id
    assert user_in_db[0].user_source == "fence"

def test_throw_not_found_soft_deleted_user(session, register_user):
    #create active user
    email_11 = f"user_11@{__name__}.com"
    user_id, user_email = register_user(email=email_11, name=__name__)
    new_user = create_associated_user(session, email=email_11, user_id=user_id)
    session.commit()
    user_in_db = session.query(AssociatedUser).filter_by(email=email_11).all()
    assert len(user_in_db) == 1
    assert user_in_db[0].active == True
    assert user_in_db[0].id == new_user.id
    #soft delete user
    deleted_user = update_associated_user(session, old_email=email_11, delete=True)
    session.commit()        
    user_in_db = session.query(AssociatedUser).filter_by(email=email_11).all()
    assert len(user_in_db) == 1
    assert user_in_db[0].active == False
    assert user_in_db[0].id == new_user.id
    #try to update soft deleted user and expect NotFound
    with pytest.raises(NotFound):
        updated_user = update_associated_user(session, old_email=email_11, new_user_id=user_id)
    with pytest.raises(UserError):
        updated_user = update_associated_user(session, new_user, new_user_id=user_id)

def test_update_associated_user_source(session, register_user):
    #create active user
    email_12 = f"user_12@{__name__}.com"
    user_id, user_email = register_user(email=email_12, name=__name__)
    new_user = create_associated_user(session, email=email_12, user_id=user_id, user_source="chicago")
    session.commit()
    user_in_db = session.query(AssociatedUser).filter_by(email=email_12).all()
    assert len(user_in_db) == 1
    assert user_in_db[0].active == True
    assert user_in_db[0].id == new_user.id
    assert user_in_db[0].user_source == "chicago"
    #update user_source
    updated_user = update_associated_user(session, old_email=email_12, new_user_source="fence")
    session.commit()        
    user_in_db = session.query(AssociatedUser).filter_by(email=email_12).all()
    assert len(user_in_db) == 1
    assert user_in_db[0].active == True
    assert user_in_db[0].id == new_user.id
    assert user_in_db[0].user_source == "fence"

@pytest.fixture(scope="module", autouse=True)
def associated_users(session, register_user):
    email_13 = f"user_13@{__name__}.com"
    user_id, user_email = register_user(email=email_13, name=__name__)
    user_13 = AssociatedUser(user_id=user_id, email=user_email)

    email_14 = f"user_14@{__name__}.com"
    user_id, user_email = register_user(email=email_14, name=__name__)
    user_14 = AssociatedUser(user_id=user_id, user_source="chicago", email=user_email)

    #not signed up user
    email_15 = f"user_15@{__name__}.com"
    user_15 = AssociatedUser(email=email_15, active=False)

    #delete user
    email_16 = f"user_16@{__name__}.com"
    user_id, user_email = register_user(email=email_16, name=__name__)
    user_16 = AssociatedUser(user_id=user_id, email=user_email, active=False)

    session.add_all([user_13, user_14, user_15, user_16])
    session.commit()

    yield user_13, user_14, user_15, user_16


def test_get_associated_users_by_id(session, associated_users):
    user_13, user_14, user_15, user_16 = associated_users
    fetched_user = get_associated_users(session, id=user_13.id, filter_by_active=False)
    assert len(fetched_user) == 1
    assert fetched_user[0].id == user_13.id
    assert fetched_user[0].email == user_13.email

def test_get_associated_users_by_user_id(session, associated_users):
    user_13, user_14, user_15, user_16 = associated_users
    fetched_user = get_associated_users(session, user_id=user_14.user_id, filter_by_active=False)
    assert len(fetched_user) == 1
    assert fetched_user[0].id == user_14.id
    assert fetched_user[0].email == user_14.email

def test_get_associated_users_by_email(session, associated_users):
    user_13, user_14, user_15, user_16 = associated_users
    fetched_user = get_associated_users(session, email=user_15.email, filter_by_active=False)
    assert len(fetched_user) == 1
    assert fetched_user[0].id == user_15.id
    assert fetched_user[0].email == user_15.email

def test_get_associated_users_active_filter(session, associated_users):
    user_13, user_14, user_15, user_16 = associated_users
    fetched_active_users = get_associated_users(session, active=True)
    #check user_13 and user_14 are in the fetched active users
    fetched_active_user_ids = [user.id for user in fetched_active_users]
    assert user_13.id in fetched_active_user_ids
    assert user_14.id in fetched_active_user_ids
    assert user_15.id not in fetched_active_user_ids
    assert user_16.id not in fetched_active_user_ids
    assert all(user.active for user in fetched_active_users)
    fetched_inactive_users = get_associated_users(session, active=False)
    #check user_15 and user_16 are in the fetched inactive users
    fetched_inactive_user_ids = [user.id for user in fetched_inactive_users]
    assert user_15.id in fetched_inactive_user_ids
    assert user_16.id in fetched_inactive_user_ids
    assert user_13.id not in fetched_inactive_user_ids
    assert user_14.id not in fetched_inactive_user_ids
    assert all(not user.active for user in fetched_inactive_users)

def test_get_associated_users_include_not_signed_up(session, associated_users):
    user_13, user_14, user_15, user_16 = associated_users
    fetched_users = get_associated_users(session, include_not_signed_up=True)
    #check user_13, user_14, and user_15 are in the fetched users
    print(fetched_users)
    fetched_user_ids = [user.id for user in fetched_users]
    assert user_13.id in fetched_user_ids
    assert user_14.id in fetched_user_ids
    assert user_15.id in fetched_user_ids
    assert user_16.id not in fetched_user_ids
    assert all(user.active or user.user_id is None for user in fetched_users)

def test_get_associated_users_by_user_source(session, associated_users):
    user_13, user_14, user_15, user_16 = associated_users
    fetched_users = get_associated_users(session, user_source="chicago", filter_by_active=False)
    fetched_user_ids = [user.id for user in fetched_users]
    assert user_14.id in fetched_user_ids
    assert user_13.id not in fetched_user_ids
    assert user_15.id not in fetched_user_ids
    assert user_16.id not in fetched_user_ids

def test_get_associated_users_throw_not_found(session):
    with pytest.raises(NotFound):
        get_associated_users(session, email="nonexistent_user@{__name__}.com", throw_not_found=True)

def test_get_associated_users_not_many(session, associated_users):
    user_13, user_14, user_15, user_16 = associated_users
    fetched_user = get_associated_users(session, id=user_13.id, many=False, filter_by_active=False)
    assert fetched_user.id == user_13.id
    with pytest.raises(UserError):
        get_associated_users(session, filter_by_active=False, many=False)

def test_get_associated_users_throw_user_not_signed_up_error(session, associated_users):
    user_13, user_14, user_15, user_16 = associated_users
    with pytest.raises(UserError):
        get_associated_users(session, email=user_15.email, throw_user_not_signed_up_error=True, filter_by_active=False)
    
    with pytest.raises(UserError):
        get_associated_users(session, filter_by_active=False, throw_user_not_signed_up_error=True)