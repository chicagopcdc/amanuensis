from amanuensis.models import AssociatedUser, Project, AssociatedUserRoles, ProjectAssociatedUser
from amanuensis.resources.userdatamodel import associate_user
import pytest
from amanuensis.errors import NotFound, UserError




def test_get_associated_user(session, associated_users):
    #test correct data
    data = associate_user.get_associated_user(session, 'user1@example.com')
    assert data.id == associated_users[0].id


def test_get_associated_users(session, associated_users):
    data = associate_user.get_associated_users(session, ['user1@example.com', 'user2@example.com'])
    for user in data:
        if user.id in [associated_users[0].id, associated_users[1].id]:
            assert True

def test_get_associated_user_by_id(session, associated_users):
    #test correct data
    data = associate_user.get_associated_user_by_id(session, associated_users[0].id)
    assert associated_users[0].id == data.id


def test_get_associated_users_by_id(session, associated_users):
    data = associate_user.get_associated_users_by_id(session, [associated_users[0].id, associated_users[1].id])
    for user in data:
        if user.id not in [associated_users[0].id, associated_users[1].id]:
            assert False 

def test_get_associated_users_by_user_id(session, associated_users):
    data = associate_user.get_associated_user_by_user_id(session, 1)
    assert data.id == associated_users[0].id

def test_update_associated_user(session, associated_users):
    user = session.query(AssociatedUser).filter(AssociatedUser.id == associated_users[2].id).first()
    user.email = 'updated email0'
    user.user_id = 0
    data = associate_user.update_associated_user(session, user)
    assert data == "200"
    update_user = session.query(AssociatedUser).filter(AssociatedUser.id == associated_users[2].id).first()
    assert update_user.email == 'updated email0'
    assert update_user.user_id == 0

    #test error is thrown
    fake_user = AssociatedUser(id=-1)
    with pytest.raises(NotFound) as e:
        associate_user.update_associated_user(session, fake_user)


# def test_update_associated_users(session, associated_users):
#     user1 = session.query(AssociatedUser).filter(AssociatedUser.id == associated_users[2].id).first()
#     user1.email = 'updated email-1'
#     user1.user_id = -1

#     user2 = session.query(AssociatedUser).filter(AssociatedUser.id == associated_users[3].id).first()
#     user2.email = 'updated email-2'
#     user2.user_id = -2

#     # data = associate_user.update_associated_users(session, [user1, user2])
#     # assert data == "200"

#     update_user1 = session.query(AssociatedUser).filter(AssociatedUser.id == associated_users[2].id).first()
#     assert update_user1.email == 'updated email-1'
#     assert update_user1.user_id == -1

#     update_user2 = session.query(AssociatedUser).filter(AssociatedUser.id == associated_users[3].id).first()
#     assert update_user2.email == 'updated email-2'
#     assert update_user2.user_id == -2


def test_add_associated_user(session, associated_users, projects, delete_project_has_associated_user):
    role_id = session.query(AssociatedUserRoles.id).filter(AssociatedUserRoles.code == "METADATA_ACCESS").first()[0]
    project_id = projects[0].id
    #test incorrect
    with pytest.raises(UserError) as e:
        associate_user.add_associated_user(session, project_id, None, None, role_id)

    data = associate_user.add_associated_user(session, project_id, 'test@email.com', 5, role_id)

    project_associated_user = session.query(ProjectAssociatedUser).filter(ProjectAssociatedUser.project_id == project_id).first()

    assert data.id == project_associated_user.associated_user.id

def test_add_associated_user_to_project(session, associated_users, projects, delete_project_has_associated_user):
    role_id = session.query(AssociatedUserRoles.id).filter(AssociatedUserRoles.code == "METADATA_ACCESS").first()[0]
    project_id = projects[0].id
    associated_user = session.query(AssociatedUser).filter(AssociatedUser.id == associated_users[0].id).first()
    
    data = associate_user.add_associated_user_to_project(session, associated_user, project_id, role_id)

    project_associated_user = session.query(ProjectAssociatedUser).filter(ProjectAssociatedUser.project_id == project_id).first()

    assert data.id == project_associated_user.associated_user.id










    



