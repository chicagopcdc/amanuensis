import pytest
from amanuensis.resources.userdatamodel.associated_users import get_associated_users, update_associated_user, create_associated_user
from amanuensis.errors import NotFound, InternalError
from amanuensis.models import AssociatedUser
from unittest.mock import MagicMock, patch

@pytest.fixture(scope="module", autouse=True)
def s3(app_instance):
    mock_s3_client = MagicMock()
    # Mock methods you use
    mock_s3_client.create_bucket.return_value = None
    mock_s3_client.list_buckets.return_value = {'Buckets': []}
    mock_s3_client.delete_object.return_value = None
    mock_s3_client.list_objects_v2.return_value = {'Contents': []}

    with patch.object(app_instance.s3_boto, 's3_client', mock_s3_client):
        yield mock_s3_client

@pytest.mark.order(1)
def test_create_associated_users(session, register_user):

    #test create user with email and user_id
    email_1 = f"user_1@{__name__}.com"
    user_id, user_email = register_user(email=email_1, name=__name__)

    new_user = create_associated_user(session, email=email_1, user_id=user_id)
    user_1 = get_associated_users(session, email=email_1, many=False)
    assert new_user.email == user_1.email
    assert new_user.user_id == user_id
    assert new_user.user_source == "fence"
    assert new_user.active == True


    #test create user with email only
    email_2 = f"user_2@{__name__}.com"
    user_id, user_email = register_user(email=email_2, name=__name__)
    new_user = create_associated_user(session, email=user_email)
    user_1 = get_associated_users(session, email=email_2, many=False, filter_by_active=False)

    assert user_1.email == user_email
    assert user_1.user_id == None
    assert user_1.user_source == None
    assert user_1.active == False


    #test block create duplicate user
    created_user = create_associated_user(session, email=f"user_1@{__name__}.com")
    get_associated_users(session, email=f"user_1@{__name__}.com", many=False)


@pytest.mark.order(2)
def test_update_associated_user(session, register_user):
    user_id, user_email = register_user(email=f"user_1@{__name__}.com", name=__name__)
    updated_user = update_associated_user(session, old_email=user_email, new_user_id=user_id)

    assert updated_user.user_id == user_id
    assert updated_user.email == user_email

    user_id, user_email = register_user(email=f"user_3@{__name__}.com", name=__name__)
    user_3 = create_associated_user(session, email=f"user_3@{__name__}.com", user_id=user_id)

    updated_user = update_associated_user(session, user=user_3, new_user_id=user_id, old_user_id=user_3.user_id)
    assert updated_user.user_id == user_id
    assert updated_user.email == user_email

    updated_user = update_associated_user(session, user=user_3, new_user_id=None, old_user_id=user_id)
    assert updated_user.user_id == user_3.user_id
    assert updated_user.email == user_email

    #test wrong type
    with pytest.raises(InternalError):
        update_associated_user(session, user="wrong type", new_user_id=5)



@pytest.mark.order(3)
def test_delete_associated_user(session, register_user):

    deleted_user = update_associated_user(session, old_email=f"user_1@{__name__}.com", delete=True)
    assert deleted_user.active == False

    with pytest.raises(NotFound):
        get_associated_users(session, email=f"user_1@{__name__}.com", many=False, throw_not_found=True)

    #read deleted user

    readded_user = create_associated_user(session, email=f"user_1@{__name__}.com")

    assert readded_user.active
    assert get_associated_users(session, email=f"user_1@{__name__}.com", many=False, throw_not_found=True)