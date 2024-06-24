import pytest 
from amanuensis.models import ConsortiumDataContributor, Project, Request, RequestState, State
from amanuensis.resources.userdatamodel import get_request_by_consortium, get_requests, get_request_by_id, get_requests_by_project_id, update_request_state
from sqlalchemy import desc

def test_get_requests(session):
    data = get_requests(session, 1)
    assert len(data) == 3
    for request in data:
        assert request.project.user_id == 1
    data = get_requests(session, 2)
    assert len(data) == 3
    for request in data:
        assert request.project.user_id == 2

def test_get_requests_by_consortium(session):
    data = get_request_by_consortium(session, None, "TEST1")
    assert len(data) == 3
    for request in data:
        assert request.consortium_data_contributor.code == "TEST1"

def test_get_request_by_id(session, requests):
    data = get_request_by_id(session, 1, requests.id)
    assert data.id == requests.id


def test_get_requests_by_project_id(session, projects, requests):
    data = get_requests_by_project_id(session, projects[0].id)
    assert data[0].id == requests.id

def test_update_request_state(session, request_has_state, states, requests, delete_request_has_state):
    update_request_state(session, requests, states[1])
    data = session.query(RequestState).filter(RequestState.request == requests).order_by(desc(RequestState.create_date)).first()
    assert data.state.code == "STATE2"


#create 3 consortiums
#create 3 projects with two users 
#project one has one request with con1 and user1
#project two has two requests with con1, con2 and user1
#project three has three requests with con1, con2, con3 and user2
