from collections import defaultdict

import flask
from cdislogging import get_logger

from amanuensis.config import config
from amanuensis.resources import fence
from amanuensis.resources import userdatamodel as udm
from amanuensis.schema import AssociatedUserSchema
from amanuensis.errors import UserError, NotFound
from amanuensis.models import AssociatedUserRoles

logger = get_logger(__name__)

__all__ = [
    "update_role",
    "add_associated_users",
    "get_codes_for_roles",
]


def update_role(project_id, user_id, email, role):
    with flask.current_app.db.session as session:
        ret = udm.update_associated_users(session, project_id, user_id, email, role)
        return ret

def get_codes_for_roles():
    with flask.current_app.db.session as session:
        roles = udm.get_associated_user_roles(session)
        return {data.role: data.code for data in roles}


def add_associated_users(users, role=None):
   # users variable format: [{project_id: "", id: "", email: ""},{}]
    users = [defaultdict(lambda: None, user) for user in users]

    with flask.current_app.db.session as session:
        associated_user_schema = AssociatedUserSchema(many=True)
        ret = []

        for user in users:
            fence_user = None
            amanuensis_user = None

            # FENCE Retrieve the users information from the Fence DB
            fence_user_by_email = None
            fence_user_by_id = None
            if "id" in user:
                fence_user_by_id = fence.fence_get_users(config, ids=[user["id"]])["users"]
                fence_user_by_id = fence_user_by_id[0] if len(fence_user_by_id) == 1 else None
            elif "email" in user:
                fence_user_by_email = fence.fence_get_users(config, usernames=[user["email"]])["users"]
                fence_user_by_email = fence_user_by_email[0] if len(fence_user_by_email) == 1 else None  
            # Check for discrepancies in case the user submitted both id and email instead of just one of the two
            if fence_user_by_email and fence_user_by_id:
                if fence_user_by_email["id"] != fence_user_by_id["id"] or fence_user_by_email["name"] != fence_user_by_id["name"]:
                    raise UserError(
                        "Invalid input - The ID and the email has to be for the same user. Only one is required. {} and {} don't match the same person in Fence.".format(user["id"], user["email"])
                    )

            # AMANUENSIS Retrieve the users from the Amanuensis DB
            associated_user_by_email = None
            associated_user_by_id = None
            if "id" in user:
                associated_user_by_id = udm.associate_user.get_associated_users_by_id(session, [user["id"]])
                associated_user_by_id = associated_user_by_id[0] if len(associated_user_by_id) == 1 else None
            elif "email" in user:
                associated_user_by_email = udm.associate_user.get_associated_users(session, [user["email"]])
                associated_user_by_email = associated_user_by_email[0] if len(associated_user_by_email) == 1 else None  
            # Check for discrepancies in case the user submitted both id and email instead of just one of the two
            if associated_user_by_email and associated_user_by_id:
                if associated_user_by_email["user_id"] != associated_user_by_id["user_id"] or associated_user_by_email["email"] != associated_user_by_id["email"]:
                    raise UserError(
                        "Invalid input - The ID and the email has to be for the same user. Only one is required. {} and {} don't match the same person in Amanuensis".format(user["id"], user["email"])
                    )

            # Check if the user exists in fence, if it doesn't send email to the user letting him/her know they need to register in the portal to be able to download the data once they are ready.
            if not fence_user_by_email and not fence_user_by_id:
                #TODO send notification to the user about registering in the portal to see the data / and potentially create the user in fence programmatically
                logger.info("The user {} has not created an account in the commons yet".format(user["id"] if "id" in user else user["email"]))
            fence_user = fence_user_by_id if fence_user_by_id else fence_user_by_email
            
            #get the foreign key for the role
            if not role:
                role_id = session.query(AssociatedUserRoles.id).filter(AssociatedUserRoles.code == "METADATA_ACCESS").first()[0]
            else:
                try:
                    role_id = session.query(AssociatedUserRoles.id).filter(AssociatedUserRoles.code == role).first()[0]
                except TypeError:
                    raise NotFound("input role is not a valid option")
            # Check if the user exists in amanuensis, if it does check it is in sync with fence and update if needed, if it doesn't add it using the fence info
            if not associated_user_by_email and not associated_user_by_id:
                # Create the user in amanuensis
                if fence_user:
                    user["email"] = fence_user["name"]
                    user["id"] = fence_user["id"]
                logger.info("Creting new Associated user")
                ret.append(
                    udm.associate_user.add_associated_user(
                        session,
                        project_id=user["project_id"],
                        email=user["email"],
                        user_id=user["id"],
                        role_id=role_id
                    )
                )
            else:
                amanuensis_user = associated_user_by_id if associated_user_by_id else associated_user_by_email
                updated = False
                if amanuensis_user.email != fence_user["name"]:
                    amanuensis_user.email = fence_user["name"]
                    updated = True
                if amanuensis_user.user_id != fence_user["id"]:
                    amanuensis_user.user_id = fence_user["id"]
                    updated = True

                if updated:
                    #Update amanuensis associated_user
                    udm.associate_user.update_associated_user(session, amanuensis_user)

                # add user to project
                ret.append(
                    udm.associate_user.add_associated_user_to_project(
                        session,
                        associated_user=amanuensis_user,
                        project_id=user["project_id"],
                        role_id=role_id
                    )
                )

        associated_user_schema.dump(ret)
        return ret
