from sqlalchemy import func, or_
import amanuensis

from sqlalchemy.orm import aliased


from amanuensis.errors import NotFound, UserError
from amanuensis.models import (
    Project,
    Search,
    AssociatedUser,
    ProjectAssociatedUser,
    ASSOCIATED_USER_ROLES,
    RequestState,
)
from amanuensis.resources.userdatamodel.userdatamodel_request import (
    get_requests_by_project_id,
)

__all__ = [
    "create_project",
    "update_project",
    "get_project_by_consortium",
    "get_project_by_user",
    "get_project_by_id",
    "get_associated_users",
    "update_associated_users",
    "update_project_date",
]


def get_project_by_consortium(current_session, consortium, logged_user_id):
    return (
        current_session.query(Project)
        .join(Project.requests)
        .join(Request.consortium_data_contributor)
        .filter_by(code=consortium)
        .all()
    )


def get_project_by_user(current_session, logged_user_id, logged_user_email):
    return current_session.query(Project).filter(Project.active == True).join(Project.associated_users).filter(or_(Project.user_id == logged_user_id, AssociatedUser.user_id == logged_user_id, AssociatedUser.email == logged_user_email)).all()


def get_project_by_id(current_session, project_id):
    # assoc_users = aliased(AssociatedUser, name='associated_user_2')

          # .join(dict_code_type, dict_code_type.codeValue == Device.deviceType) \

    # return current_session.query(Project).filter(
    #         # Project.user_id == logged_user_id,
    #         Project.id == project_id
    #     ).join(Project.associated_users).join(ProjectAssociatedUser, Project.associated_users_roles).join(assoc_users, assoc_users.id == ProjectAssociatedUser.associated_user_id).first()

    return current_session.query(Project).filter(
            Project.id == project_id
        ).join(
            ProjectAssociatedUser, Project.associated_users_roles
        ).join(
            AssociatedUser, ProjectAssociatedUser.associated_user).first()



def create_project(current_session, user_id, description, name, institution, searches, requests, associated_users):
    """
    Creates a project with an associated auth_id and storage access
    """
    new_project = Project(
        user_id=user_id,
        user_source="fence",
        description=description,
        institution=institution,
        name=name,
    )

    current_session.add(new_project)
    current_session.flush()
    new_project.searches.extend(searches)
    new_project.requests.extend(requests)
    new_project.associated_users.extend(associated_users)

    # current_session.flush()
    # current_session.add(new_project)
    # current_session.merge(new_project)

    # current_session.flush()
    # current_session.refresh(new_project)
    current_session.commit()

    return new_project


def update_project(current_session, project_id, approved_url=None, searches=None):
    if not approved_url and not searches:
        return {
            "code": 200,
            "error": "Nothing has been updated, no new values have been received by the function.",
        }

    data = {}
    if approved_url:
        data["approved_url"] = approved_url
    if searches and isinstance(searches, list) and len(searches) > 0:
        data["searches"] = searches

    # TODO check that at least one has changed
    num_updated = (
        current_session.query(Project).filter(Project.id == project_id).update(data)
    )
    if num_updated > 0:
        return {"code": 200, "updated": int(project_id)}
    else:
        return {
            "code": 500,
            "error": "Nothing has been updated, check the logs to see what happened during the transaction.",
        }


def get_associated_users(current_session, emails):
    if not emails:
        return []
    return current_session.query(AssociatedUser).filter(AssociatedUser.email.in_(emails)).all()


def update_associated_users(current_session, project_id, id, email, role):
    user_by_id = None
    user_by_email = None

    if id:
        user_by_id = current_session.query(ProjectAssociatedUser).filter(ProjectAssociatedUser.project_id == project_id).join(AssociatedUser, ProjectAssociatedUser.associated_user).filter(AssociatedUser.user_id == id).first()
        # q = s.query(Parent).join(Child, Parent.child).filter(Child.value > 20)

    if email:
        user_by_email = current_session.query(ProjectAssociatedUser).filter(ProjectAssociatedUser.project_id == project_id).join(AssociatedUser, ProjectAssociatedUser.associated_user).filter(AssociatedUser.email == email).first()
        # user_by_email = ccurrent_session.query(AssociatedUser).filter(
        #     AssociatedUser.id == id
        # ).join(Project, AssociatedUser.projects).filter(
        #     Project.id == project_id
        # ).first()

    # print(user_by_id)
    # print(user_by_email)
    # print(email)
    # print(id)
    if user_by_id:
        user_by_id.role = role
    elif user_by_email:
        user_by_email.role = role
    else:
        raise NotFound("No user associated with project {} found.".format(project_id))

    # current_session.commit()
    current_session.flush()
    return "200"


def update_project_date(session, project_id, new_update_date):
    requests = get_requests_by_project_id(session, project_id)
    if not requests:
        raise NotFound(
            "There are no requests associated to this project or there is no project. id: {}".format(
                project_id
            )
        )

    for request in requests:
        create_date = request.request_has_state[-1].create_date
        if create_date <= new_update_date:
            request.update_date = new_update_date
            request_state = request.request_has_state[-1]
            session.query(RequestState).filter(
                RequestState.request_id == request_state.request_id,
                RequestState.create_date == create_date,
                RequestState.state_id == request_state.state_id,
            ).update({"update_date": new_update_date})
            session.flush()
        else:
            raise UserError("The new update_date must be later than the create date.")
    return requests


# def delete_project(current_session, project_name):
#     """
#     Delete the project from the database
#     The project should have no buckets in use
#     """
#     proj = current_session.query(Project).filter(Project.name == project_name).first()

#     if not proj:
#         return {"result": "error, project not found"}

#     buckets = (
#         current_session.query(ProjectToBucket)
#         .filter(ProjectToBucket.project_id == proj.id)
#         .first()
#     )

#     if buckets:
#         msg = (
#             "error, project still has buckets associated with it. Please"
#             " remove those first and then retry."
#         )
#         return {"result": msg}

#     storage_access = current_session.query(StorageAccess).filter(
#         StorageAccess.project_id == proj.id
#     )
#     """
#     Find the users that only belong to this project
#     and store them to be removed
#     """
#     accesses = current_session.query(AccessPrivilege).filter(
#         AccessPrivilege.project_id == proj.id
#     )
#     users_to_remove = []
#     for access in accesses:
#         num = (
#             current_session.query(func.count(AccessPrivilege.project_id))
#             .filter(AccessPrivilege.user_id == access.user_id)
#             .scalar()
#         )
#         if num == 1:
#             for storage in storage_access:
#                 provider = (
#                     current_session.query(CloudProvider)
#                     .filter(CloudProvider.id == storage.provider_id)
#                     .first()
#                 )
#                 usr = (
#                     current_session.query(User)
#                     .filter(User.id == access.user_id)
#                     .first()
#                 )
#                 users_to_remove.append((provider, usr))
#                 current_session.delete(usr)
#         current_session.delete(access)
#     for storage in storage_access:
#         current_session.delete(storage)
#     current_session.delete(proj)
#     return {"result": "success", "users_to_remove": users_to_remove}
