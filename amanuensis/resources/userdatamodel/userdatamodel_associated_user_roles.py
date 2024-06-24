from amanuensis.models import AssociatedUserRoles
from amanuensis.errors import NotFound
import flask
from cdislogging import get_logger



__all__ = [
    "get_associated_user_role_by_code",
    "get_all_associated_user_roles"
]

def get_all_associated_user_roles(current_session):
    return current_session.query(AssociatedUserRoles).all()



def get_associated_user_role_by_code(code, current_session=None, throw_error=True):
    if current_session:
        role = current_session.query(AssociatedUserRoles).filter(AssociatedUserRoles.code == code).first()
    else:
        with flask.current_app.db.session as session:
            role = session.query(AssociatedUserRoles).filter(AssociatedUserRoles.code == code).first()
    if not role and throw_error:
        raise NotFound(f"{code} is not an availible role") 
    return role