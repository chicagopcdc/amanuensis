from collections import defaultdict
from amanuensis.errors import  UserError, NotFound
from amanuensis.resources.fence import fence_get_users
from amanuensis.resources.userdatamodel.associated_users import update_associated_user, create_associated_user, get_associated_users
from amanuensis.resources.userdatamodel.associated_user_roles import get_associated_user_roles
from amanuensis.resources.userdatamodel.project_has_associated_user import create_project_associated_user, update_project_associated_user, get_project_associated_users
from amanuensis.resources.userdatamodel.project import get_projects
from amanuensis.config import config
from cdislogging import get_logger


logger = get_logger(__name__)

__all__ = [
    "add_associated_users",
    "remove_associated_user"
]


def add_associated_users(session, users, role=None):
    
    ROLE = get_associated_user_roles(session, code=config["ASSOCIATED_USER_ROLE_DEFAULT"] if not role else role, many=False)
    ret = []
    input_users = [defaultdict(lambda: None, user) for user in users]
    for input_user in input_users:

        email = input_user["email"] if "email" in input_user else None
        id = input_user["id"] if "id" in input_user else None
        
        if "project_id" not in input_user:
            raise UserError("project_id is required to add user to project")
        
        get_projects(session, id=input_user["project_id"], throw_not_found=True, many=False)

        if email:
            fence_user = fence_get_users(usernames=[email])["users"]

            if fence_user:
                if id and id != fence_user[0]["id"]:
                    raise UserError(f"The user id {id} does not match the email {email} in the commons")
                else:
                    id = fence_user[0]["id"]
            
            elif id:
                raise UserError(f"The user id {id} does not match the email {email} in the commons")

            else:
                logger.info("The user {} has not created an account in the commons yet".format(email))
                #TODO send message via aws to the email address inviting them to sign up          
        
        elif id:
            fence_user = fence_get_users(ids=[id])["users"]

            if fence_user:
                email = fence_user[0]["username"]

            else:
                raise UserError(f"The user id {id} does not exist in the commons")

        else:
            raise UserError("The user id or email is required")
        

        associated_user = create_associated_user(session, email=email, user_id=id)

        if not associated_user.user_id and id:
            update_associated_user(session, user=associated_user, new_user_id=id)

        project_associated_user = create_project_associated_user(session, project_id=input_user["project_id"], associated_user_id=associated_user.id, role_id=ROLE.id)

        ret.append(project_associated_user)

    return ret


def remove_associated_user(session, project_id, user_id=None, email=None):
    project = get_projects(session, id=project_id, many=False, throw_not_found=True)
   
    
    
    if email:
        project_user = get_project_associated_users(session, project_id=project_id, associated_user_email=email, many=False, throw_not_found=True)

    else:
        project_user = get_project_associated_users(session, project_id=project_id, associated_user_user_id=user_id, many=False)

        #this covers a situation if a user signs up but never goes to data request page
        if not project_user:
            try:
                fence_user_email = fence_get_users(ids=[user_id])["users"][0]["username"]
            except Exception as e:
                raise NotFound(f"User {user_id} not found in commons")
            
            project_user = get_project_associated_users(session, project_id=project_id, associated_user_email=fence_user_email, many=False, throw_not_found=True)
            update_associated_user(session, old_email=fence_user_email, new_user_id=user_id)
    
    if project.user_id == project_user.associated_user.user_id:
        raise UserError("You can't remove the owner from the project")
    

    
    updated_project_user = update_project_associated_user(session, project_associated_user=project_user, delete=True)


    return updated_project_user