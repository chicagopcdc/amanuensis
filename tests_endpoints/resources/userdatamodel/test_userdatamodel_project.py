import pytest

from amanuensis.resources.userdatamodel import userdatamodel_project as project 
from amanuensis.models import Project, AssociatedUser, Request, ConsortiumDataContributor, ProjectAssociatedUser, AssociatedUserRoles
from amanuensis.errors import NotFound
from userportaldatamodel.models import ProjectSearch


def test_get_projects_by_consortium(session, consortiums, projects):
    data = project.get_project_by_consortium(session, consortiums[1].code, None)
    assert len(data) == 2
    for pro in data:
        assert pro.id in [projects[1].id, projects[2].id]

# def test_get_project_by_user(session, associated_users, projects, delete_project_has_associated_user, roles):
#     project_user = ProjectAssociatedUser(project=projects[0], associated_user=associated_users[0], role=roles[0])
#     session.add(project_user)
#     session.commit()
#     data = project.get_project_by_user(session, 1, 'user1@example.com')
#     assert len(data) == 2
#     assert data[0].id == projects[0].id
#     assert data[1].id == projects[1].id

def test_get_project_by_id(session, projects):
    assert projects[0].id == project.get_project_by_id(session, None, projects[0].id).id


# def test_create_project(session, requests, associated_users, searches): 
#     data = project.create_project(session, -1, "TEST", "TEST", "TEST", searches, [requests], associated_users)

#     assert data.user_id == -1

#     project_id = session.query(Project.id).filter(Project.user_id == -1).first()[0]

#     #session.query(ProjectSearch)
#     session.query(ProjectAssociatedUser).filter(ProjectAssociatedUser.project_id == project_id).delete()    
#     session.query(Request).filter(Request.project_id == project_id).delete()
#     session.query(Project).filter(Project.id == project_id).delete()

#     session.commit()


def test_update_project(session, projects, searches):
    data = project.update_project(session, projects[0].id)
    assert data == {"code": 200, "error": "Nothing has been updated, no new values have been received by the function.",}
    
    data = project.update_project(session, projects[0].id, approved_url="test.com")
    assert session.query(Project.id).filter(Project.approved_url == "test.com").first()[0] == projects[0].id

    #TODO fix this when this is supported
    #this currently doesnt work throws error passing a list
    # data = project.update_project(session, projects[0].id, "test.com", searches)
    # assert data == {"code": 200, "updated": int(projects[0].id)}

# def test_update_associated_users(session, projects, associated_users, roles, delete_project_has_associated_user):

#     user_project = ProjectAssociatedUser(project=projects[0], associated_user=associated_users[0], role=roles[0])
#     session.add(user_project)
#     session.commit()

#     data = project.update_associated_users(session, projects[0].id, 1, None, roles[1].code)
#     assert user_project.role.code == roles[1].code

#     data = project.update_associated_users(session, projects[0].id, 1, None, None)
#     assert user_project.active == False


#     data = project.update_associated_users(session, projects[0].id, None, 'user1@example.com', roles[0].code)
#     assert user_project.role.code == roles[0].code
#     assert user_project.active == True

#     data = project.update_associated_users(session, projects[0].id, None, 'user1@example.com', None)
#     assert user_project.active == False


def test_update_project_date():
    pass