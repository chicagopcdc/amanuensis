import pytest
from amanuensis.resources.userdatamodel.associated_users import get_associated_users, update_associated_user, create_associated_user
from amanuensis.errors import NotFound, InternalError
from amanuensis.models import AssociatedUser





@pytest.mark.order(1)
def test_create_associated_users(session, add_user_to_fence):

    #test create user with email
    new_user = create_associated_user(session, email=f"user_1@{__name__}.com")
    user_1 = get_associated_users(session, email=f"user_1@{__name__}.com", many=False)

    assert new_user.email == user_1.email

    #test create user with email and user_id
    user_id, user_email = add_user_to_fence(email=f"user_2@{__name__}.com", name=__name__)
    new_user = create_associated_user(session, email=user_email, user_id=user_id)

    assert new_user.email == user_email
    assert new_user.user_id == user_id

    #test block create duplicate user
    created_user = create_associated_user(session, email=f"user_1@{__name__}.com")
    get_associated_users(session, email=f"user_1@{__name__}.com", many=False)


@pytest.mark.order(2)
def test_update_associated_user(session, add_user_to_fence):
    user_id, user_email = add_user_to_fence(email=f"user_1@{__name__}.com", name=__name__)

    updated_user = update_associated_user(session, old_email=user_email, new_user_id=user_id)

    assert updated_user.user_id == user_id
    assert updated_user.email == user_email


    user_3 = create_associated_user(session, email=f"user_3@{__name__}.com")
    user_id, user_email = add_user_to_fence(email=f"user_3@{__name__}.com", name=__name__)
    updated_user = update_associated_user(session, user=user_3, new_user_id=user_id)
    assert updated_user.user_id == user_id
    assert updated_user.email == user_email

    #test wrong type
    with pytest.raises(InternalError):
        update_associated_user(session, user="wrong type", new_user_id=5)



@pytest.mark.order(3)
def test_delete_associated_user(session, add_user_to_fence):

    deleted_user = update_associated_user(session, old_email=f"user_1@{__name__}.com", delete=True)
    assert deleted_user.active == False

    with pytest.raises(NotFound):
        get_associated_users(session, email=f"user_1@{__name__}.com", many=False, throw_not_found=True)

    #read deleted user

    readded_user = create_associated_user(session, email=f"user_1@{__name__}.com")

    assert readded_user.active
    assert get_associated_users(session, email=f"user_1@{__name__}.com", many=False, throw_not_found=True)