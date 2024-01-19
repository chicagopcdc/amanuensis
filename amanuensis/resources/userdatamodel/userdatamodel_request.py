from sqlalchemy import func


from amanuensis.errors import NotFound, UserError
from amanuensis.models import (
    Request,
    Project,
    RequestState
)

__all__ = [
    "get_requests",
    "get_request_by_id",
    "get_request_by_consortium",
    "get_requests_by_project_id",
    "update_request_state",
]


def get_requests(current_session, user_id):
    return current_session.query(Request).join(Request.project).filter_by(user_id=user_id).all()

def get_request_by_consortium(current_session, user_id, consortium):
    return current_session.query(Request).join(Request.consortium_data_contributor).filter_by(code=consortium).all()

def get_request_by_id(current_session, user_id, request_id):
    return current_session.query(Request).filter_by(id=request_id).join(Request.project).filter_by(user_id=user_id).first()


def get_requests_by_project_id(current_session, project_id):
    return current_session.query(Request).filter(Request.project_id == project_id).all()

def update_request_state(
    current_session, request, state
):
    """
    Updates the state for a request
    """
    req_state = RequestState()
    req_state.request = request
    req_state.state = state
    current_session.add(req_state)
    # request.states.append(state)
    current_session.flush()
    return request

