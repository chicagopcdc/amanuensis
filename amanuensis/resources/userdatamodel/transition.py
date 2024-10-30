from amanuensis.models import Transition, State
from sqlalchemy.orm import aliased
from amanuensis.errors import NotFound, UserError

def get_transition_graph(current_session, state=None, reverse=False, final_states=False):
    #if reverse is true it will return the directed graph with every edge reversed

    src_state_alias = aliased(State)
    dst_state_alias = aliased(State)

    result = (
        current_session.query(src_state_alias.code, dst_state_alias.code)
                       .join(Transition, Transition.state_src_id == src_state_alias.id)
                       .join(dst_state_alias, Transition.state_dst_id == dst_state_alias.id)
                       .all()
    )

    if final_states:
        src = set()
        dst = set()
        for src_state, dst_state in result:
            src.add(src_state)
            dst.add(dst_state)
        return dst.difference(src)


    transition_graph = {}
    
    if reverse:
        for src_state, dst_state in result:
            transition_graph[dst_state] = transition_graph.get(dst_state, [])
            transition_graph[dst_state].append(src_state)
    else:
        for src_state, dst_state in result:
            transition_graph[src_state] = transition_graph.get(src_state, [])
            transition_graph[src_state].append(dst_state)

    if state is not None:
        return transition_graph.get(state, [])
    
    return transition_graph

    