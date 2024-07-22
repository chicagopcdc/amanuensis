from logging import getLogger
from sqlalchemy import func, desc
from sqlalchemy.orm import aliased
from amanuensis.resources.message import send_admin_message
from amanuensis.resources.userdatamodel.userdatamodel_project import get_project_by_id
from amanuensis.resources.userdatamodel.userdatamodel_request import update_request_state
from amanuensis.errors import NotFound, UserError
from amanuensis.config import config
from amanuensis.models import (
    State,
    ConsortiumDataContributor,
    Transition,
    Request,
    RequestState
)
__all__ = [
    "create_state",
    "get_all_states",
    "update_project_state",
    "get_state_by_id",
    "get_state_by_code",
    "get_final_states",
    "get_transition_graph"
]

logger = getLogger(__name__)


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
    return current_session.query(State).filter(State.code != 'DEPRECATED').all()



# TODO move these 2 functions in the resources, there is logic here, the userdatamodel folder should contain mostly DB operation
def notify_user_project_status_update(current_session, project_id, consortiums):
    """
    Notify the users when project state changes.
    """
    project = get_project_by_id(current_session, 1, project_id)
    email_subject = f"Project {project.name}: Data Delivered"
    email_body = f"The project f{project.name} data was delivered."

    return send_admin_message(project, consortiums, email_subject, email_body)


def get_latest_request_state_by_id(current_session, requests=None, request_ids=[]):
    #filter out any request whos state is depreicated
    #requests are request objects
    #request_ids are ints
    if requests and request_ids:
        logger.error("both request and request_ids were passed to get_latest_request_state_by_id returning []")
        return []
    elif request_ids:
        request_ids = [request_ids] if not isinstance(request_ids, list) else request_ids
    elif requests:
        requests = [requests] if not isinstance(requests, list) else requests
        request_ids = [request.id for request in requests]
    else:
        logger.error("No requests were passed to get_latest_request_state_by_id returning []")
        return []

    subquery = (
        current_session.query(
            RequestState.request_id,
            func.max(RequestState.create_date).label("max_create_date")
        )
        .filter(RequestState.request_id.in_(request_ids))
        .group_by(RequestState.request_id)
        .subquery()
    )

    sq = aliased(subquery)
    rs = aliased(RequestState)

    result = (
        current_session.query(rs)
        .join(State, rs.state)
        .filter(rs.request_id == sq.c.request_id, rs.create_date == sq.c.max_create_date)
        .filter(State.code != "DEPRECATED")
        .all()
    )
    return result

def get_transition_graph(current_session, reverse=False):
    #if reverse is true it will return the directed graph with every edge reversed

    src_state_alias = aliased(State)
    dst_state_alias = aliased(State)

    result = (
        current_session.query(src_state_alias.code, dst_state_alias.code)
                       .join(Transition, Transition.state_src_id == src_state_alias.id)
                       .join(dst_state_alias, Transition.state_dst_id == dst_state_alias.id)
                       .all()
    )

    transition_graph = {}
    if reverse:
        for src_state, dst_state in result:
            transition_graph[dst_state] = transition_graph.get(dst_state, [])
            transition_graph[dst_state].append(src_state)
    else:
        for src_state, dst_state in result:
            transition_graph[src_state] = transition_graph.get(src_state, [])
            transition_graph[src_state].append(dst_state)
    
    return transition_graph

def get_final_states(current_session):
    src_state_alias = aliased(State)
    dst_state_alias = aliased(State)

    result = (
        current_session.query(src_state_alias.code, dst_state_alias.code)
                       .join(Transition, Transition.state_src_id == src_state_alias.id)
                       .join(dst_state_alias, Transition.state_dst_id == dst_state_alias.id)
                       .all()
    )
    src = set()
    dst = set()
    for src_state, dst_state in result:
        src.add(src_state)
        dst.add(dst_state)
    return dst.difference(src)
    

def update_project_state(
    current_session, requests, state, project_id
):
    """
    Updates the state for a project, including all requests in the project. Notifies users when the state changes to DATA_DELIVERED.
    """
    final_states = get_final_states(current_session)
    current_request_states = get_latest_request_state_by_id(current_session, requests)
    updated_requests = []
    for request_state in current_request_states:
        if request_state.state.code == state.code:
            logger.info(
                "Request {} is already in state {}. No need to change.".format(
                    request_state.request.id, state.code
                )
            )
        elif request_state.state.code in final_states:
            raise UserError(
                "Cannot change state of request {} from {} because it's a final state".format(
                    request_state.request.id, state.code
                )
            )
        else:
            update_request_state(current_session, request_state.request, state)
            updated_requests.append(request_state.request)

    current_session.flush()
    return updated_requests
#END TODO
