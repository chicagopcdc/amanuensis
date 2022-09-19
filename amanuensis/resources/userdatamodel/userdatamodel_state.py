from logging import getLogger
from sqlalchemy import func, desc
from amanuensis.resources.message import send_admin_message
from amanuensis.resources.userdatamodel.userdatamodel_project import get_project_by_id
from amanuensis.errors import NotFound, UserError
from amanuensis.models import (
    State,
    ConsortiumDataContributor,
)
__all__ = [
    "create_state",
    "get_all_states",
    "create_consortium",
    "get_state_by_id",
    "get_state_by_code",
]

logger = getLogger(__name__)


def create_consortium(current_session, name, code):
    """
    Creates a consortium
    """
    new_consortium = ConsortiumDataContributor(name=name, code=code)

    current_session.add(new_consortium)
    current_session.flush()

    return new_consortium


def create_state(current_session, name, code):
    """
    Creates a state
    """
    new_state = State(name=name, code=code)

    current_session.add(new_state)
    # current_session.commit()
    current_session.flush()

    return new_state


def get_state_by_id(current_session, state_id):
    return current_session.query(State).filter(State.id == state_id).first()


def get_state_by_code(current_session, code):
    return current_session.query(State).filter(State.code == code).first()


def get_all_states(current_session):
    return current_session.query(State).all()
