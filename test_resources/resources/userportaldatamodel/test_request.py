import pytest 
from amanuensis.resources.userdatamodel.request import get_requests, create_request
from amanuensis.resources.userdatamodel.project import create_project
from amanuensis.resources.userdatamodel.consortium_data_contributor import get_consortiums
from amanuensis.resources.userdatamodel.associated_users import create_associated_user


@pytest.fixture(scope="session")
def project_and_requests(session, add_user_to_fence):
    user_id, user_email = add_user_to_fence(email=f"user_1@{__name__}.com", name=__name__)
    user_2_id, user_2_email = add_user_to_fence(email=f"user_2@{__name__}.com", name=__name__)
    create_associated_user(session, email=user_email, user_id=user_id)
    create_associated_user(session, email=user_2_email, user_id=user_2_id)
    INRG = get_consortiums(session, code="INRG")
    INSTRUCT = get_consortiums(session, code="INSTRUCT")
    INTERACT = get_consortiums(session, code="INTERACT")
    project1 = create_project(session, user_id=user_id, name=f"{__name__}_1", description=f"test in {__name__}", institution=f"{__name__}")
    request_1 = create_request(session, project1.id, INRG[0].id)
    request_2 = create_request(session, project1.id, INSTRUCT[0].id)

    project2 = create_project(session, user_id=user_2_id, name=f"{__name__}_2", description=f"test in {__name__}", institution=f"{__name__}")
    request_3 = create_request(session, project2.id, INRG[0].id)
    request_4 = create_request(session, project2.id, INSTRUCT[0].id)
    request_5 = create_request(session, project2.id, INTERACT[0].id)

    yield project1, project2, request_1, request_2, request_3, request_4, request_5

@pytest.mark.order(1)
def test_create_request(project_and_requests, session):
    project1, project2, request_1, request_2, request_3, request_4, request_5 = project_and_requests
    assert request_1.project_id == project1.id
    assert request_2.project_id == project1.id
    assert request_3.project_id == project2.id
    assert request_4.project_id == project2.id
    assert request_5.project_id == project2.id

@pytest.mark.order(2)
def test_get_request(project_and_requests, session):
    project1, project2, request_1, request_2, request_3, request_4, request_5 = project_and_requests
    retrieved_requests = get_requests(session, consortiums="INRG", project_id=[project1.id, project2.id], many=True)
    assert len(retrieved_requests) == 2
    assert retrieved_requests[0].project_id == project1.id
    assert retrieved_requests[1].project_id == project2.id

    retrieved_requests = get_requests(session, project_id=project2.id, many=True)
    assert len(retrieved_requests) == 3
    assert retrieved_requests[0].project_id == project2.id
    assert retrieved_requests[1].project_id == project2.id
    assert retrieved_requests[2].project_id == project2.id

    retrieved_requests = get_requests(session, id=[request_1.id, request_2.id], many=True)
    assert len(retrieved_requests) == 2
    assert retrieved_requests[0].id == request_1.id
    assert retrieved_requests[1].id == request_2.id

    retrieved_requests = get_requests(session, user_id=project1.user_id, many=True)
    assert len(retrieved_requests) == 2
    assert retrieved_requests[0].project_id == project1.id
    assert retrieved_requests[1].project_id == project1.id

    retrieved_requests = get_requests(session, id=request_3.id, many=False)
    assert retrieved_requests.id == request_3.id

    retrieved_requests = get_requests(session, id=[request_3.id, request_4.id], many=True)
    assert len(retrieved_requests) == 2
    assert retrieved_requests[0].id == request_3.id
    assert retrieved_requests[1].id == request_4.id