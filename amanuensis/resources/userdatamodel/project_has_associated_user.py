from amanuensis.errors import NotFound, UserError, InternalError
from amanuensis.models import ProjectAssociatedUser, AssociatedUser, AssociatedUserRoles
from amanuensis.resources.userdatamodel.associated_user_roles import get_associated_user_roles
from cdislogging import get_logger
from amanuensis.config import config

logger = get_logger(logger_name=__name__)


def get_project_associated_users(
        current_session, 
        project_id=None,
        associated_user_id=None,
        active=True,
        role_id=None,
        role_code=None,
        associated_user_email=None,
        associated_user_user_id=None,
        throw_not_found=False,
        many=True,
        filter_by_active=True
        ):
    
    logger.info(f"get_project_associated_user: {locals()}")

    project_associated_user = current_session.query(ProjectAssociatedUser)

    if filter_by_active:
        project_associated_user = project_associated_user.filter(ProjectAssociatedUser.active == active)

    if project_id is not None:
        project_id = [project_id] if not isinstance(project_id, list) else project_id
        project_associated_user = project_associated_user.filter(ProjectAssociatedUser.project_id.in_(project_id))

    if associated_user_id is not None:
        associated_user_id = [associated_user_id] if not isinstance(associated_user_id, list) else associated_user_id
        project_associated_user = project_associated_user.filter(ProjectAssociatedUser.associated_user_id.in_(associated_user_id))

    if role_id is not None:
        role_id = [role_id] if not isinstance(role_id, list) else role_id
        project_associated_user = project_associated_user.filter(ProjectAssociatedUser.role_id.in_(role_id))

    if role_code is not None:
        role_code = [role_code] if not isinstance(role_code, list) else role_code
        project_associated_user = project_associated_user.filter(ProjectAssociatedUser.role.has(AssociatedUserRoles.code.in_(role_code)))

    if associated_user_user_id is not None:
        associated_user_user_id = [associated_user_user_id] if not isinstance(associated_user_user_id, list) else associated_user_user_id
        project_associated_user = project_associated_user.filter(ProjectAssociatedUser.associated_user.has(AssociatedUser.user_id.in_(associated_user_user_id)))

    if associated_user_email is not None:
        associated_user_email = [associated_user_email] if not isinstance(associated_user_email, list) else associated_user_email
        project_associated_user = project_associated_user.filter(ProjectAssociatedUser.associated_user.has(AssociatedUser.email.in_(associated_user_email)))
    
    project_associated_user = project_associated_user.all()

    if throw_not_found and not project_associated_user:
        raise NotFound(f"The user is not in the list of associated_users that signed the DUA. Please reach out to pcdc_help@lists.uchicago.edu")

    if not many:
        if len(project_associated_user) > 1:
            raise UserError("Multiple ProjectAssociatedUsers found")
        else:
            project_associated_user = project_associated_user[0] if project_associated_user else project_associated_user

    return project_associated_user


def update_project_associated_user(
        current_session, 
        project_associated_user=None, 
        project_id=None, 
        associated_user_id=None, 
        role_id=None,
        delete=False
        ):
    
    if project_associated_user:
        if not isinstance(project_associated_user, ProjectAssociatedUser):
            raise InternalError("project_associated_user must be a ProjectAssociatedUser")
    else:
        project_associated_user = get_project_associated_users(
            current_session, 
            project_id=project_id, 
            associated_user_id=associated_user_id, 
            many=False,
            throw_not_found=True
        )

    project_associated_user.active = True if not delete else False
    project_associated_user.role_id = role_id if role_id else project_associated_user.role_id

    current_session.commit()

    return project_associated_user

def create_project_associated_user(
        current_session, 
        project_id, 
        associated_user_id,
        role_id):

    

    project_associated_user = get_project_associated_users(
        current_session, 
        project_id=project_id, 
        associated_user_id=associated_user_id,
        filter_by_active=False, 
        many=False
    )

    if project_associated_user:
        if not project_associated_user.active:
            project_associated_user.active = True
            project_associated_user.role_id = role_id
            logger.info(f"ProjectAssociatedUser has been readded to the project")
        else:
            logger.info(f"ProjectAssociatedUser already exists: {project_id} {associated_user_id}")

    else:
        new_project_associated_user = ProjectAssociatedUser(
            project_id = project_id,
            associated_user_id = associated_user_id,
            role_id = role_id,
            active = True
        )

        current_session.add(new_project_associated_user)
    
    current_session.commit()
    
    return project_associated_user
    
    