from amanuensis.errors import NotFound, UserError
from amanuensis.models import AssociatedUser, ProjectAssociatedUser
from amanuensis.resources.userdatamodel.userdatamodel_associated_user_roles import get_associated_user_role_by_code
from amanuensis.config import config
from cdislogging import get_logger

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
    "get_project_associated_user",
    "change_project_user_status",
    "update_user_role"
]

logger = get_logger(logger_name=__name__)

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

def get_project_associated_user(current_session, project_id, id=None, email=None):
    user_by_id = None
    user_by_email = None

    if id:
        user_by_id = current_session.query(ProjectAssociatedUser).filter(ProjectAssociatedUser.project_id == project_id).join(AssociatedUser, ProjectAssociatedUser.associated_user).filter(AssociatedUser.user_id == id).first()
        # q = s.query(Parent).join(Child, Parent.child).filter(Child.value > 20)

    if email:
        user_by_email = current_session.query(ProjectAssociatedUser).filter(ProjectAssociatedUser.project_id == project_id).join(AssociatedUser, ProjectAssociatedUser.associated_user).filter(AssociatedUser.email == email).first()
    
    if not user_by_email and not user_by_id:
        return
    
    if user_by_email and user_by_id and (user_by_email.associated_user.id != user_by_id.associated_user.id):
        raise UserError(
                "Invalid input - The ID and the email has to be for the same user. Only one is required. {} and {} don't match the same person in Fence.".format(id, email)
            )

    user = user_by_id if user_by_id else user_by_email

    return user

def update_user_role(current_session, project_associated_user, code):
    role = get_associated_user_role_by_code(code, current_session=current_session)
    if not project_associated_user.active:
        raise UserError(f"{project_associated_user.associated_user.email} is no longer an associated user of this project, they must be re-added before changing their data access")
    else:
        project_associated_user.role = role
    
    current_session.flush()
    return f"{project_associated_user.associated_user.email} now has {code}"

def change_project_user_status(current_session, project_associated_user, status):
    
    if not status:
        if project_associated_user.project.user_id == project_associated_user.associated_user.user_id:
            raise UserError("You cannot remove the owner of the project")
        update_user_role(current_session, project_associated_user, config["ASSOCIATED_USER_ROLE_DEFAULT"])
    project_associated_user.active = status
    current_session.flush()
    return "{user} has been {condition}".format(user=project_associated_user.associated_user.email, condition=("added" if status else "removed"))



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
    
    #check if project_user already exists
    user = get_project_associated_user(current_session, project_id, email=associated_user.email)
    if user:
        if not user.active:
            change_project_user_status(current_session, user, True)
            logger.info(f"{associated_user.email} has been readded to the project")
        return user

    new_project_user = ProjectAssociatedUser(
        project_id = project_id,
        associated_user_id = associated_user.id,
        role_id=role_id
    )

    current_session.add(new_project_user)
    current_session.commit()
    return associated_user



