from amanuensis.resources.userdatamodel.request_has_state import get_request_states, create_request_state
from amanuensis.resources.userdatamodel.request import create_request
from amanuensis.resources.userdatamodel.state import get_states
from amanuensis.resources.userdatamodel.project import create_project
from amanuensis.resources.userdatamodel.consortium_data_contributor import get_consortiums
from amanuensis.resources.userdatamodel.associated_users import create_associated_user
import pytest

@pytest.fixture(scope="session", autouse=True)
def create_test_data(session, register_user):
    user_id, user_email = register_user(email=f"user_1@{__name__}.com", name=__name__)
    project = create_project(session, name=f"{__name__}", description="test", institution="test", user_id=user_id)
    INRG = get_consortiums(session, code="INRG")
    INSTRUCT = get_consortiums(session, code="INSTRUCT")
    INTERACT = get_consortiums(session, code="INTERACT")
    request_1 = create_request(session, project.id, INRG[0].id)
    request_2 = create_request(session, project.id, INSTRUCT[0].id)
    request_3 = create_request(session, project.id, INTERACT[0].id)

    yield request_1, request_2, request_3


@pytest.mark.order(1)
def test_create_request_state(session, create_test_data):
    request_1, request_2, request_3 = create_test_data
    IN_REVIEW = get_states(session, code="IN_REVIEW", many=False)

    assert create_request_state(session, request_1.id, IN_REVIEW.id)
    assert create_request_state(session, request_2.id, IN_REVIEW.id)
    assert create_request_state(session, request_3.id, IN_REVIEW.id)

    APPROVED = get_states(session, code="APPROVED", many=False)

    assert create_request_state(session, request_1.id, APPROVED.id)

    #block create duplicate
    assert create_request_state(session, request_1.id, APPROVED.id)
    assert len(get_request_states(session, request_id=request_1.id)) == 2

    REVISION = get_states(session, code="REVISION", many=False)

    assert create_request_state(session, request_2.id, REVISION.id)

    DEPRECATED = get_states(session, code="DEPRECATED", many=False)

    assert create_request_state(session, request_1.id, DEPRECATED.id)


@pytest.mark.order(2)
def test_get_request_state(session, create_test_data):
    request_1, request_2, request_3 = create_test_data
    IN_REVIEW = get_states(session, code="IN_REVIEW", many=False)
    REVISION = get_states(session, code="REVISION", many=False)
    DEPRECATED = get_states(session, code="DEPRECATED", many=False)

    # print(get_request_states(session, request_id=request_3.id, latest=True, many=False))
    # from amanuensis.schema import RequestStateSchema
    # request_schema = RequestStateSchema(many=True)
    # print(request_schema.dump(get_request_states(session)))
    assert get_request_states(session, request_id=request_3.id, latest=True, many=False).state_id == IN_REVIEW.id
    assert get_request_states(session, request_id=request_2.id, latest=True, many=False).state_id == REVISION.id
    assert get_request_states(session, request_id=request_1.id, latest=True, many=False).state_id == DEPRECATED.id

    assert len(get_request_states(session, request_id=request_1.id, latest=True, filter_out_depricated=True)) == 0
    assert len(get_request_states(session, request_id=request_2.id, latest=True, filter_out_depricated=True)) == 1

    assert len(get_request_states(session, request_id=[request_1.id, request_2.id, request_3.id], state_id=IN_REVIEW.id)) == 3