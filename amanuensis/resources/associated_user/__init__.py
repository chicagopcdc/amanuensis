from collections import defaultdict
from amanuensis.errors import  UserError
from amanuensis.schema import AssociatedUserSchema
from amanuensis.resources.fence import fence_get_users
from amanuensis.resources.userdatamodel.associated_users import update_associated_user, create_associated_user
from amanuensis.resources.userdatamodel.associated_user_roles import get_associated_user_roles
from amanuensis.resources.userdatamodel.project_has_associated_user import create_project_associated_user
from amanuensis.config import config
from cdislogging import get_logger


logger = get_logger(__name__)

__all__ = [
    "add_associated_users",
]


def add_associated_users(session, users, role=None):
    
    ROLE = get_associated_user_roles(session, code=config["ASSOCIATED_USER_ROLE_DEFAULT"] if not role else role, many=False)
    associated_user_schema = AssociatedUserSchema(many=True)
    ret = []
    input_users = [defaultdict(lambda: None, user) for user in users]
    for input_user in input_users:

    
        
        if "project_id" not in input_user:
            raise UserError("The project_id is required to add user to project")

        if "email" in input_user:
            fence_user = fence_get_users(usernames=[input_user["email"]])["users"]

            if fence_user:
                if input_user["id"] and input_user["id"] != fence_user[0]["id"]:
                    raise UserError(f"The user id {input_user['id']} does not exist in the commons")
                else:
                    input_user["id"] = fence_user[0]["id"]

            else:
                logger.info("The user {} has not created an account in the commons yet".format(input_user["id"] if "id" in input_user else input_user["email"]))
                #TODO send message via aws to the email address inviting them to sign up          
        
        elif "id" in input_user:
            fence_user = fence_get_users(ids=[input_user["id"]])["users"]

            if fence_user:
                input_user["email"] = fence_user[0]["name"]

            else:
                raise UserError(f"The user id {input_user['id']} does not exist in the commons")

        else:
            raise UserError("The user id or email is required")
        

        associated_user = create_associated_user(session, email=input_user["email"], user_id=input_user["id"])

        if not associated_user.user_id and input_user["id"]:
            update_associated_user(session, user=associated_user, new_user_id=input_user["id"])

        project_associated_user = create_project_associated_user(session, project_id=input_user["project_id"], associated_user_id=associated_user.id, role_id=ROLE.id)

        ret.append(project_associated_user)

    return associated_user_schema.dump(ret)
