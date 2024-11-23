from amanuensis.errors import NotFound, UserError
from amanuensis.models import (
    State
)

from cdislogging import get_logger
logger = get_logger(__name__)

__all__ = [
    "create_state",
    "get_states"
]


def get_states(current_session, id=None, name=None, code=None, throw_not_found=False, many=True, filter_out_depricated=False):
    states = current_session.query(State)

    logger.info(f"get_states: {locals()}")

    if id is not None:
        id = [id] if not isinstance(id, list) else id
        states = states.filter(State.id.in_(id))
    
    if name:
        name = [name] if not isinstance(name, list) else name
        states = states.filter(State.name.in_(name))

    if code:
        code = [code] if not isinstance(code, list) else code
        states = states.filter(State.code.in_(code))
    
    if filter_out_depricated:
        states = states.filter(State.code != "DEPRECATED")

    states = states.all()

    if throw_not_found and not states:
        raise NotFound(f"No states found")

    if not many:
        if len(states) > 1:
            raise UserError(f"More than one state found check inputs")
        else:
            states = states[0] if states else None
    
    return states


def create_state(current_session, name, code):

    state = get_states(current_session, code=code, many=False)
    if state:
        logger.info(f"State {code} already exists, skipping")
    
    else:
    
        state = State(
                        name=name,
                        code=code
                    )
        
        current_session.add(
            state
        )

        current_session.flush()

    return state