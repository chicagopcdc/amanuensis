import pytest
from amanuensis.resources.userdatamodel.state import create_state, get_states
from amanuensis.errors import NotFound, UserError
from amanuensis.models import State


def test_create_state(session):

    session.query(State).filter(State.code == f"{__name__}").delete()

    state = create_state(session, code=f"{__name__}", name=f"{__name__}")

    assert state.code == get_states(session, code=f"{__name__}")[0].code

    assert state.name == get_states(session, name=f"{__name__}", many=False).name


    


    session.commit()


