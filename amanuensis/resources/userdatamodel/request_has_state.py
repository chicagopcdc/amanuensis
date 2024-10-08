from amanuensis.models import RequestState, Request, State
from cdislogging import get_logger
from amanuensis.errors import NotFound, UserError, InternalError
from sqlalchemy import func
from sqlalchemy import and_
from sqlalchemy.orm import aliased


logger = get_logger(__name__)

def get_request_states(
        current_session, 
        request_id=None, 
        state_id=None,
        latest=False,
        filter_out_depricated=False,
        throw_not_found=False,
        many=True):
    
    """
    Gets the latest request state for a given request id

    Args:
        current_session (Session): the current DB session
        request_id (int): the id of the request
        state_id (int): the id of the state
        latest (bool): if True, only return the latest request state
        throw_not_found (bool): if True, raise a NotFound error if no request state is found
        many (bool): if True, return all request states

    Returns:
        list: a list of RequestState objects
    """
    request_state = current_session.query(RequestState)

    if request_id is not None:
        request_id = [request_id] if not isinstance(request_id, list) else request_id
        request_state = request_state.filter(RequestState.request_id.in_(request_id))
    
    if latest:
        subquery = current_session.query(
            RequestState.request_id,
            func.max(RequestState.create_date).label("max_create_date")
        ) \
        .group_by(RequestState.request_id) \
        .subquery()

        request_state = request_state.filter(RequestState.request_id == subquery.c.request_id, RequestState.create_date == subquery.c.max_create_date)
    
    if state_id is not None:
        state_id = [state_id] if not isinstance(state_id, list) else state_id
        request_state = request_state.filter(RequestState.state_id.in_(state_id))
    
    
    if filter_out_depricated:
        request_state = request_state.filter(RequestState.state.has(State.code != "DEPRECATED"))

    request_state = request_state.all()

    if throw_not_found and not request_state:
        raise NotFound(f"No requests found")

    if not many:
        if len(request_state) > 1:
            raise UserError(f"More than one request found check inputs")
        else:
            request_state = request_state[0] if request_state else request_state
    
    return request_state

def create_request_state(current_session, request_id, state_id):
    """
    Creates a new request state

    Args:
        session (Session): the current DB session
        request_id (int): the id of the request
        state_id (int): the id of the state

    Returns:
        RequestState: a newly created request state
    """
    
    request_state = get_request_states(current_session, request_id=request_id, state_id=state_id, latest=True)

    if request_state:
        logger.info(f"Request {request_id} already has state {state_id}")
    
    else:
        request_state = RequestState(request_id=request_id, state_id=state_id)
        current_session.add(request_state)
        current_session.commit()

    return request_state
