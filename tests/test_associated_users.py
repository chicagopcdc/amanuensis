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

@pytest.fixture
def find_fence_user_custom(fence_users, find_fence_user):
    def get_fence_user(usernames=None, ids=None):
        # Build the dict in the format the old find_fence_user expects
        if usernames and ids:
            raise ValueError("Only one of 'usernames' or 'ids' should be set")
        query = {}
        if usernames:
            query["usernames"] = usernames
        elif ids:
            query["ids"] = ids
        else:
            query = {}  # empty dict for no input
        
        return find_fence_user(query)
    return get_fence_user

@pytest.fixture(autouse=True)
def patch_fence_get_users(monkeypatch, find_fence_user_custom):
    monkeypatch.setattr(
        "amanuensis.resources.userdatamodel.associated_users.fence_get_users",
        find_fence_user_custom
    )


@pytest.fixture
def user_email():
    return "user_1@test.com"

@pytest.fixture
def user_id():
    return 12345

def test_create_associated_user_with_registration(session, register_user, user_email):
    user_id, email = register_user(email=user_email, name="Test User")
    new_user = create_associated_user(session, email=user_email, user_id=user_id)
    assert new_user.user_id == user_id
    assert new_user.user_source == "fence"
    fetched = get_associated_users(session, email=user_email, many=False)
    assert fetched.email == user_email

def test_create_associated_user_without_registration(session):
    email = "nonregistered@test.com"
    new_user = create_associated_user(session, email=email, user_id=9999999)
    assert new_user.user_id is None
    assert new_user.user_source is None

def test_create_duplicate_associated_user(session, register_user, user_email):
    user_id, email = register_user(email=user_email, name="Test User")
    old_user = create_associated_user(session, email=user_email, user_id=user_id)
    user = create_associated_user(session, email=user_email)
    assert old_user.id == user.id

def test_update_associated_user_by_email(session, register_user, user_email):
    user_id, email = register_user(email=user_email, name="Test User")
    create_associated_user(session, email=user_email)
    updated_user = update_associated_user(session, old_email=user_email, new_user_id=user_id)
    assert updated_user.user_id == user_id
    assert updated_user.email == user_email

def test_update_associated_user_by_instance(session, register_user):
    email = "user_2@test.com"
    user_id, _ = register_user(email=email, name="Test User 2")
    user = create_associated_user(session, email=email)
    updated_user = update_associated_user(session, user=user, new_user_id=user_id)
    assert updated_user.user_id == user_id
    assert updated_user.email == email

def test_update_associated_user_without_registration(session,register_user, user_email):
    user_id, email = register_user(email= user_email, name="Test User")
    user = create_associated_user(session, email=user_email, user_id=user_id)

    nonregistered_id = 99999999
    updated_user = update_associated_user(session, user=user, new_user_id=nonregistered_id)
    assert updated_user.user_id is None
    assert updated_user.user_source is None
    assert updated_user.active is False

def test_update_associated_user_to_registered(session, register_user):
    email = "nonregistered_update@test.com"
    user = create_associated_user(session, email=email, user_id=99999999) 
    assert user.user_id is None
    assert user.user_source is None
    assert user.active is False

    new_user_id, _ = register_user(email=email, name="Registered User")
    updated_user = update_associated_user(session, user=user, new_user_id=new_user_id)

    assert updated_user.user_id == new_user_id
    assert updated_user.user_source == "fence"
    assert updated_user.active is True

def test_update_associated_user_wrong_type(session):
    with pytest.raises(InternalError):
        update_associated_user(session, user="not_a_user_instance", new_user_id=5)

def test_delete_associated_user(session, register_user):
    user_email = "delete_user_test@test.com"
    user_id, email = register_user(email=user_email, name="Test User")
    user = create_associated_user(session, email=user_email, user_id=user_id)
    deleted_user = update_associated_user(session, old_email=user_email, delete=True)
    assert deleted_user.active is False
    with pytest.raises(NotFound):
        get_associated_users(session, email=user_email, many=False, throw_not_found=True)

def test_readd_deleted_associated_user(session, user_email):
    user = create_associated_user(session, email=user_email)
    assert user.active
    fetched = get_associated_users(session, email=user_email, many=False, throw_not_found=True)
    assert fetched.active

def test_get_associated_users_not_found(session):
    with pytest.raises(NotFound):
        get_associated_users(session, email="doesnotexist@test.com", many=False, throw_not_found=True)