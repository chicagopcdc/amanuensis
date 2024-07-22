import flask
from cdislogging import get_logger
from amanuensis.errors import NotFound, UserError
from amanuensis.resources import userdatamodel as udm
from amanuensis.resources.userdatamodel.userdatamodel_project import get_project_by_id
from amanuensis.resources.message import send_admin_message
from datetime import datetime
from amanuensis.config import config
from amanuensis.schema import (
    StateSchema,
    RequestSchema,
    ConsortiumDataContributorSchema,
)
from amanuensis.errors import NotFound


logger = get_logger(__name__)

__all__ = [
    "create_state",
    "get_all_states",
    "update_project_state",
    "create_consortium",
    "get_by_code",
]


def create_state(name, code):
    with flask.current_app.db.session as session:
        state_schema = StateSchema()
        state = udm.create_state(session, name, code)
        state_schema.dump(state)
        return state


def get_all_states():
    with flask.current_app.db.session as session:
        return udm.get_all_states(session)


def get_by_code(code, session=None):
    if session:
        return udm.get_state_by_code(session, code)
    else:
        with flask.current_app.db.session as session:
            return udm.get_state_by_code(session, code)


def update_project_state(project_id, state_id, consortium_list=None):
    with flask.current_app.db.session as session:
        if consortium_list:
            requests = udm.get_requests_by_project_id_consortium(session, project_id, consortium_list)
        else:
            requests = udm.get_requests_by_project_id(session, project_id)
        if not requests:
            raise NotFound(
                "There are no requests associated to this project or there is no project. id: {}".format(
                    project_id
                )
            )
        
        state = udm.get_state_by_id(session, state_id)
        if not state:
            raise NotFound("The state with id {} has not been found".format(state_id))

        request_schema = RequestSchema(many=True)
        
        requests = udm.update_project_state(
            session, requests, state, project_id 
        )

        if state.code in config["NOTIFY_STATE"] and requests:
            notify_user_project_status_update(
                session,
                project_id,
                [updated_request.consortium_data_contributor.code for updated_request in requests]
            )
        
        request_schema.dump(requests)
        return requests


def notify_user_project_status_update(current_session, project_id, consortiums):
    """
    Notify the users when project state changes.
    """
    project = get_project_by_id(current_session, project_id)
    email_subject = f"Project {project.name}: Data Delivered"
    email_body = f"The project f{project.name} data was delivered."

    return send_admin_message(project, consortiums, email_subject, email_body)


def create_consortium(name, code):
    with flask.current_app.db.session as session:
        consortium_schema = ConsortiumDataContributorSchema()
        consortium = udm.create_consortium(session, code, name)
        consortium_schema.dump(consortium)
        return consortium
