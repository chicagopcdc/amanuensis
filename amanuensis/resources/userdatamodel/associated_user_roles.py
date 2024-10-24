from amanuensis.models import AssociatedUserRoles
from amanuensis.errors import NotFound, UserError
from cdislogging import get_logger

logger = get_logger(logger_name=__name__)

__all__ = [
    "get_associated_user_roles"
]

def get_associated_user_roles(current_session, id=None, role=None, code=None, throw_not_found=False, many=True):
    
    logger.info(f"get_associated_user_roles: {locals()}")
    
    roles = current_session.query(AssociatedUserRoles)

    if id is not None:
        id = [id] if not isinstance(id, list) else id
        roles = roles.filter(AssociatedUserRoles.id.in_(id))
    
    if role:
        role = [role] if not isinstance(role, list) else role
        roles = roles.filter(AssociatedUserRoles.role.in_(role))

    if code:
        code = [code] if not isinstance(code, list) else code
        roles = roles.filter(AssociatedUserRoles.code.in_(code))

    roles = roles.all()

    if throw_not_found and not roles:
        raise NotFound(f"No Role Found")
        

    if not many:
        if len(roles) > 1:
            raise UserError(f"More than one Role found check inputs")
        else:
            roles = roles[0] if roles else None
    
    return roles