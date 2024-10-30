from amanuensis.errors import NotFound, UserError, InternalError
from amanuensis.models import AssociatedUser
from cdislogging import get_logger


logger = get_logger(logger_name=__name__)

__all__ = [
    "get_associated_users",
    "update_associated_user",
    "create_associated_user"
]




def get_associated_users(current_session, 
                         id=None, 
                         user_id=None, 
                         email=None, 
                         active=True, 
                         user_source=None, 
                         filter_by_active=True, 
                         many=True, 
                         throw_not_found=False):
    
    logger.info(f"get_associated_users: {locals()}")
    
    users = current_session.query(AssociatedUser)

    if filter_by_active:
        users = users.filter(AssociatedUser.active == active)

    if id is not None:
        id = [id] if not isinstance(id, list) else id
        users = users.filter(AssociatedUser.id.in_(id))
    
    if user_id is not None:
        user_id = [user_id] if not isinstance(user_id, list) else user_id
        users = users.filter(AssociatedUser.user_id.in_(user_id))
    
    if email:
        email = [email] if not isinstance(email, list) else email
        users = users.filter(AssociatedUser.email.in_(email))
    
    if user_source:
        user_source = [user_source] if not isinstance(user_source, list) else user_source
        users = users.filter(AssociatedUser.user_source.in_(user_source))

    users = users.all()

    if throw_not_found and not users:
        raise NotFound(f"No users found")

    if not many:
        if len(users) > 1:
            raise UserError(f"More than one user found check inputs")
        else:
            users = users[0] if users else None
    
    return users

#Update User old_<parameter> will be used to search for an object 
# new_<parameter> will be used as new value
# if new_<parameter> is None, the current value will be used
def update_associated_user(current_session, 
                           user=None, 
                           old_email=None, 
                           old_user_id=None, 
                           old_user_source="fence",
                           new_email=None,
                           new_user_id=None,
                           new_user_source="fence",
                           delete=False):
    if user:
    
        if not isinstance(user, AssociatedUser):
        
            logger.error("user must be an instance of AssociatedUser")
        
            raise InternalError("input must be correct type")

    else:

        user = get_associated_users(current_session, 
                                    email=old_email, 
                                    user_id=old_user_id, 
                                    user_source=old_user_source, 
                                    many=False, 
                                    throw_not_found=True
                )
    
    user.user_id = new_user_id if new_user_id else user.user_id
    user.user_source = new_user_source if new_user_source else user.user_source
    user.email = new_email if new_email else user.email
    user.active = True if not delete else False

    current_session.commit()

    return user

#Create and Reactivate Users
def create_associated_user(current_session, email, user_id=None, user_source="fence"):

    user = get_associated_users(current_session, 
                                      email=email, 
                                      many=False,
                                      filter_by_active=False
                                      )

    if user:
        if not user.active:
            user.active = True
            logger.info(f"User {user.email} has been reactivated")
        else: 
            logger.info(f"User {user.email} already exists, skipping")
    else:
        new_user = AssociatedUser(
                        email=email, 
                        user_id=user_id, 
                        user_source=user_source, 
                        active=True
                    )
        current_session.add(
            new_user
        )

        

        logger.info(f"User {new_user} has been created")
    
    current_session.commit()
    
    return user if user else new_user
