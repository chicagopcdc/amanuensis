import flask
import json
from cdislogging import get_logger

from amanuensis.resources import userdatamodel as udm
from amanuensis.config import config
from amanuensis.schema import StateSchema, RequestSchema, ConsortiumDataContributorSchema, AssociatedUserSchema
from amanuensis.errors import NotFound


logger = get_logger(__name__)

__all__ = [
    "update_role",
    "add_associated_users",
]


def update_role(project_id, user_id, email, role):
    with flask.current_app.db.session as session:  
        ret = udm.update_associated_users(session, project_id, user_id, email, role)
        return ret

def add_associated_users(users):
    with flask.current_app.db.session as session:
        associated_user_schema = AssociatedUserSchema(many=True)
        ret = []
        for user in users:
            ret.append(udm.add_associated_user(session, user["project_id"], user["email"] if "email" in user else None, user["id"] if "id" in user else None))
        associated_user_schema.dump(ret)
        return ret



