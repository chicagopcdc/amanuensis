from sqlalchemy import func




from amanuensis.errors import NotFound, UserError
from amanuensis.models import (
    Project,
    Search
)

__all__ = [
    "create_project",
    "update_project",
    "get_project_by_consortium",
    "get_project_by_user",
    "get_project_by_id"
]


def get_project_by_consortium(current_session, consortium, logged_user_id):
    return current_session.query(Project).join(Project.requests).join(Request.consortium_data_contributor).filter_by(code=consortium).all()


def get_project_by_user(current_session, logged_user_id):
    return current_session.query(Project).filter_by(user_id=logged_user_id).all()


def get_project_by_id(current_session, logged_user_id, project_id):
    return current_session.query(Project).filter(
            Project.user_id == logged_user_id,
            Project.id == project_id
        ).first()


def create_project(current_session, user_id, description, name, institution, searches, requests):
    """
    Creates a project with an associated auth_id and storage access
    """
    new_project = Project(user_id=user_id,
                        user_source="fence",
                        description=description,
                        institution=institution,
                        name=name
                    )


    current_session.add(new_project)
    current_session.flush()
    new_project.searches.extend(searches)
    new_project.requests.extend(requests)

    # current_session.flush()
    # current_session.add(new_project)
    # current_session.merge(new_project)

    # current_session.flush()
    # current_session.refresh(new_project)
    current_session.commit()
    
    return new_project


def update_project(current_session, project_id, approved_url=None, searches=None):
    if not appoved_url and not searches:
        return {"code": 200, "error": "Nothing has been updated, no new values have been received by the function."}

    data = {}
    if url:
        data['approved_url'] = approved_url
    if searches and isinstance(searches, list) and len(searches) > 0:
        data["searches"] = searches

    #TODO check that at least one has changed
    num_updated = current_session.query(Project).filter(
        Project.id == project_id
    ).update(data)
    if  num_updated > 0:
        return  {"code": 200, "updated": int(project_id)}
    else:
        return {"code": 500, "error": "Nothing has been updated, check the logs to see what happened during the transaction."}


 



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

