import pytest
from amanuensis.resources.userdatamodel.project import get_projects, create_project, update_project
from amanuensis.errors import NotFound
from amanuensis.models import Project
from amanuensis.resources.userdatamodel.associated_users import create_associated_user

@pytest.fixture(scope="module", autouse=True)
def users(session, register_user):
    user_id, user_email = register_user(email=f"user_1@{__name__}.com", name=__name__)
    admin_id, admin_email = register_user(email=f"admin@{__name__}.com", name=__name__, role="admin")

    user = create_associated_user(session, email=user_email, user_id=user_id)
    admin = create_associated_user(session,email=admin_email, user_id=admin_id)

    yield user, admin


@pytest.mark.order(1)
def test_create_project(session, users):

    project = create_project(session, 
                             name=f"test_{__name__}", 
                             description=f"test in {__name__}",  
                             institution=f"{__name__}", 
                             user_id=users[0].user_id)
    
    assert project.name == f"test_{__name__}"
    assert project.description == f"test in {__name__}"
    assert project.institution == f"{__name__}"
    assert project.user_id == users[0].user_id
    assert project.user_source == "fence"

@pytest.mark.order(2)
def test_update_project(session, users):

    old_project = get_projects(session, user_id=users[0].user_id, many=False, throw_not_found=True)

    updated_project = update_project(session,
                                     id=old_project.id,
                                     first_name="test",
                                     last_name="test",
                                     user_id=users[0].user_id,
                                     user_source="fence",
                                     description="test",
                                     institution="test",
                                     name=f"updated_{__name__}",
                                     approved_url="test"
                                     )

    assert updated_project.first_name == "test"
    assert updated_project.last_name == "test"
    assert updated_project.user_id == users[0].user_id
    assert updated_project.user_source == "fence"
    assert updated_project.description == "test"
    assert updated_project.institution == "test"
    assert updated_project.name == f"updated_{__name__}"
    assert updated_project.approved_url == "test"
    

@pytest.mark.order(3)
def test_delete_project(session, users):

    old_project = get_projects(session, user_id=users[0].user_id, many=False, throw_not_found=True)

    deleted_project = update_project(session, id=old_project.id, delete=True)

    with pytest.raises(NotFound):
        get_projects(session, user_id=users[0].user_id, many=False, throw_not_found=True)

    
