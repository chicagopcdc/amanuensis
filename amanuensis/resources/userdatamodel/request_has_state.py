from amanuensis.models import RequestState, Request, State, ConsortiumDataContributor
from cdislogging import get_logger
from amanuensis.errors import NotFound, UserError, InternalError
from sqlalchemy import func
from sqlalchemy import and_
from sqlalchemy.orm import aliased


logger = get_logger(__name__)

def get_request_states(
        current_session, 
        request_id=None, 
        project_id=None,
        consortiums=None,
        state_id=None,
        latest=False,
        order_by=False,
        order_by_create_date_desc=False,
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
        order_by (bool): if True, add ordering to the results
        order_by_create_date_desc (bool): if True, order by create date descending
        filter_out_depricated (bool): if True, filter out deprecated states
        project_id (int): the id of the project
        consortiums (list): list of consortium codes to filter by
        throw_not_found (bool): if True, raise a NotFound error if no request state is found
        many (bool): if True, return all request states

    Returns:
        list: a list of RequestState objects
    """
    request_state = current_session.query(RequestState)

    if project_id is not None:
        project_id = [project_id] if not isinstance(project_id, list) else project_id
        request_state = request_state.filter(RequestState.request.has(Request.project_id.in_(project_id)))

    if consortiums is not None:
        consortiums = [consortiums] if not isinstance(consortiums, list) else consortiums
        request_state = request_state.filter(RequestState.request.has(Request.consortium_data_contributor.has(ConsortiumDataContributor.code.in_(consortiums))))
    
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

    if order_by:
        if order_by_create_date_desc:
            request_state = request_state.order_by(RequestState.create_date.desc())

    request_state = request_state.all()

    if throw_not_found and not request_state:
        raise NotFound(f"No requests found")

    if not many:
        if len(request_state) > 1:
            raise UserError(f"More than one request found check inputs")
        else:
            request_state = request_state[0] if request_state else None
    
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
    
    request_state = get_request_states(current_session, request_id=request_id, state_id=state_id, latest=True, many=False)

    if request_state:
        logger.info(f"Request {request_id} already has state {state_id}")
    
    else:
        request_state = RequestState(request_id=request_id, state_id=state_id)
        current_session.add(request_state)
        current_session.flush()

    return request_state
