from amanuensis.errors import NotFound, UserError
from amanuensis.models import AssociatedUser, ProjectAssociatedUser

__all__ = [
    "get_associated_user",
    "get_associated_users",
    "get_associated_user_by_id",
    "get_associated_users_by_id",
    "get_associated_user_by_user_id",
    "update_associated_user",
    "update_associated_users",
    "add_associated_user",
    "add_associated_user_to_project",
]

def get_associated_user(current_session, email):
    if not email:
        return
    return current_session.query(AssociatedUser).filter(AssociatedUser.email == email).first()


def get_associated_users(current_session, emails):
    if not emails:
        return []
    return (
        current_session.query(AssociatedUser)
        .filter(AssociatedUser.email.in_(emails))
        .all()
    )


def get_associated_user_by_id(current_session, id):
    if not id:
        return
    return (
        current_session.query(AssociatedUser).filter(AssociatedUser.id==id).first()
    )


def get_associated_users_by_id(current_session, ids):
    if not ids:
        return []
    return (
        current_session.query(AssociatedUser)
        .filter(AssociatedUser.user_id.in_(ids))
        .all()
    )


def get_associated_user_by_user_id(current_session, id):
    if not id:
        return
    return (
        current_session.query(AssociatedUser)
        .filter(AssociatedUser.user_id == id)
        .first()
    )


def update_associated_user(current_session, associated_user):

    user = get_associated_user_by_id(
        current_session=current_session, id=associated_user.id
    )
    if not user:
        raise NotFound("Associated user not found.")
    
    user.email = associated_user.email
    user.user_id = associated_user.user_id

    current_session.flush()

    return "200"


def update_associated_users(current_session, associated_users):

    for user in associated_users:
        update_associated_user(
            current_session=current_session, associated_user=user
        )

    return "200"


def add_associated_user(current_session, project_id, email, user_id, role_id):
    if not user_id and not email: 
        raise UserError("Missing email and id.")

    new_user = AssociatedUser(
        user_id=user_id if user_id else None,
        user_source="fence",
        email=email if email else None,
    )

    current_session.add(new_user)
    current_session.flush()

    new_project_user = ProjectAssociatedUser(
        project_id = project_id,
        associated_user_id = new_user.id,
        role_id=role_id
    )

    current_session.add(new_project_user)
    current_session.commit()
    return new_user


def add_associated_user_to_project(current_session, associated_user, project_id, role_id):
    if not associated_user and not associated_user.id:
        raise UserError("Missing user id.")

    new_project_user = ProjectAssociatedUser(
        project_id = project_id,
        associated_user_id = associated_user.id,
        role_id=role_id
    )

    current_session.add(new_project_user)
    current_session.commit()
    return associated_user