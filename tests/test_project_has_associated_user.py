import pytest
from amanuensis.resources.userdatamodel.project_has_associated_user import get_project_associated_users, create_project_associated_user, update_project_associated_user
from amanuensis.resources.userdatamodel.associated_user_roles import get_associated_user_roles
from amanuensis.resources.userdatamodel.associated_users import create_associated_user, get_associated_users
from amanuensis.resources.userdatamodel.project import create_project
from amanuensis.errors import NotFound, UserError
from amanuensis.models import ProjectAssociatedUser


@pytest.fixture(scope="session")
def setup_project_has_associated_user(session, register_user):
    user_id, user_email = register_user(email=f"user_1@{__name__}.com", name=__name__)
    user_2_id, user_2_email = register_user(email=f"user_2@{__name__}.com", name=__name__)
    user_3_id, user_3_email = register_user(email=f"user_3@{__name__}.com", name=__name__)

    user = create_associated_user(session, email=user_email, user_id=user_id)
    user_2 = create_associated_user(session, email=user_2_email, user_id=user_2_id)
    user_3 = create_associated_user(session, email=user_3_email, user_id=user_3_id)

    project_1 = create_project(session, user_id=user_id, name=f"{__name__}_1", description=f"test in {__name__}", institution=f"{__name__}")
    project_2 = create_project(session, user_id=user_2_id, name=f"{__name__}_2", description=f"test in {__name__}", institution=f"{__name__}")

    yield project_1, project_2, user.id, user_2.id, user_3.id, user_email, user_2_email, user_3_email


@pytest.mark.order(1)
def test_create_project_has_associated_user(session, setup_project_has_associated_user):
    project_1, project_2, user_id, user_2_id, user_3_id, user_email, user_2_email, user_3_email = setup_project_has_associated_user

    DATA_ACCESS = get_associated_user_roles(session, code="DATA_ACCESS", many=False)
    METADATA_ACCESS = get_associated_user_roles(session, code="METADATA_ACCESS", many=False)

    create_project_associated_user(session, project_id=project_1.id, associated_user_id=user_id, role_id=METADATA_ACCESS.id)
    create_project_associated_user(session, project_id=project_1.id, associated_user_id=user_2_id, role_id=METADATA_ACCESS.id)

    create_project_associated_user(session, project_id=project_2.id, associated_user_id=user_id, role_id=DATA_ACCESS.id)
    create_project_associated_user(session, project_id=project_2.id, associated_user_id=user_2_id, role_id=METADATA_ACCESS.id)
    create_project_associated_user(session, project_id=project_2.id, associated_user_id=user_3_id, role_id=METADATA_ACCESS.id)
    
    #block create duplicate user
    create_project_associated_user(session, project_id=project_1.id, associated_user_id=user_id, role_id=METADATA_ACCESS.id)
    assert len(get_project_associated_users(session, project_id=project_1.id)) == 2


@pytest.mark.order(2)
def test_update_project_has_associated_user(session, setup_project_has_associated_user):
    project_1, project_2, user_id, user_2_id, user_3_id, user_email, user_2_email, user_3_email = setup_project_has_associated_user
    DATA_ACCESS = get_associated_user_roles(session, code="DATA_ACCESS", many=False)
    METADATA_ACCESS = get_associated_user_roles(session, code="METADATA_ACCESS", many=False)
    #Test Change role
    updated_user = update_project_associated_user(session, project_id=project_1.id, associated_user_id=user_id, role_id=DATA_ACCESS.id)
    assert updated_user.role_id == DATA_ACCESS.id

    #Test Delete user
    update_project_associated_user(session, project_id=project_1.id, associated_user_id=user_id, delete=True)
    with pytest.raises(NotFound):
        get_project_associated_users(session, project_id=project_1.id, associated_user_id=user_id, throw_not_found=True)

    #Reactivate user

    create_project_associated_user(session, project_id=project_1.id, associated_user_id=user_id, role_id=METADATA_ACCESS.id)
    assert len(get_project_associated_users(session, project_id=project_1.id, associated_user_id=user_id)) == 1   

@pytest.mark.order(3)
def test_get_project_has_associated_user(session, setup_project_has_associated_user):
    project_1, project_2, user_id, user_2_id, user_3_id, user_email, user_2_email, user_3_email = setup_project_has_associated_user
    assert len(get_project_associated_users(session, project_id=project_1.id)) == 2
    assert len(get_project_associated_users(session, project_id=project_2.id)) == 3

    assert len(get_project_associated_users(session, project_id=project_1.id, associated_user_id=user_id)) == 1
    assert len(get_project_associated_users(session, project_id=project_2.id, associated_user_id=user_id)) == 1
    assert len(get_project_associated_users(session, project_id=project_2.id, associated_user_id=user_2_id)) == 1
    assert len(get_project_associated_users(session, project_id=project_2.id, associated_user_id=user_3_id)) == 1

    user_1 = get_associated_users(session, email=user_email, many=False)

    assert len(get_project_associated_users(session, project_id=project_1.id, associated_user_user_id=user_1.user_id, throw_not_found=True)) == 1
    assert len(get_project_associated_users(session, project_id=project_2.id, associated_user_email=user_1.email)) == 1

    METADATA_ACCESS = get_associated_user_roles(session, code="METADATA_ACCESS", many=False)

    assert len(get_project_associated_users(session, project_id=project_2.id, role_id=METADATA_ACCESS.id)) == 2