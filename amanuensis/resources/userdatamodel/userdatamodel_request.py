from sqlalchemy import func, and_


from amanuensis.errors import NotFound, UserError
from amanuensis.models import (
    Request,
    Project,
    RequestState,
    ConsortiumDataContributor
)

__all__ = [
    "get_requests",
    "get_request_by_id",
    "get_request_by_consortium",
    "get_requests_by_project_id",
    "update_request_state",
    "get_requests_by_project_id_consortium",
]

#TODO
#could be more clear to rename some of these functions
# get_requests -> get_all_requests_by_user_id
# get_request_by_consortium -> get_all_requests_by_consortium also remove user_id as a parameter
# get_requests_by_project_id -> get_all__by_project_id
# get_request_by_id this could just be current_session.query(Request).filter_by(id=request_id).first() since request_id is the only PK
# clean up imports 

def get_requests(current_session, user_id):
    return current_session.query(Request).join(Request.project).filter_by(user_id=user_id).all()

def get_request_by_consortium(current_session, user_id, consortium):
    return current_session.query(Request).join(Request.consortium_data_contributor).filter_by(code=consortium).all()

def get_request_by_id(current_session, user_id, request_id):
    return current_session.query(Request).filter_by(id=request_id).join(Request.project).filter_by(user_id=user_id).first()

def get_requests_by_project_id(current_session, project_id):      
    return current_session.query(Request).filter(Request.project_id == project_id).all()

def get_requests_by_project_id_consortium(current_session, project_id, consortium_list):
    return (
        current_session.query(Request)
                       .filter(Request.project_id == project_id)
                       .join(ConsortiumDataContributor, Request.consortium_data_contributor)
                       .filter(ConsortiumDataContributor.code.in_(consortium_list)).all()
    )

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

