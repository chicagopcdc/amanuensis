import pytest
from amanuensis.models import Message, Project, Request, ConsortiumDataContributor
from amanuensis.resources.userdatamodel.message import get_messages, create_message
from amanuensis.errors import NotFound, UserError

@pytest.fixture(scope="module", autouse=True)
def setup(session):
    project = Project(name="test_message_project_helper")
    session.add(project)

    INRG = session.query(ConsortiumDataContributor).filter(ConsortiumDataContributor.code == "INRG").first()
    INSTRUCT = session.query(ConsortiumDataContributor).filter(ConsortiumDataContributor.code == "INSTRUCT").first()
    INTERACT = session.query(ConsortiumDataContributor).filter(ConsortiumDataContributor.code == "INTERACT").first()

    session.commit()

    yield [project, INRG, INSTRUCT, INTERACT]



def test_message_create(session, setup, register_user):
    user_id, user_email = register_user(email=f"user_1@test_message_create.com", name="test_message_create")
    request = Request(project_id=setup[0].id, consortium_data_contributor_id=setup[1].id)
    session.add(request)
    session.commit()

    message = create_message(session, sender_id=user_id, request_id=request.id, body="test_message_create")

def test_message_create_duplicate(session, setup, register_user):
    user_id, user_email = register_user(email=f"user_1@test_message_create_duplicate.com", name="test_message_create_duplicate")
    request = Request(project_id=setup[0].id, consortium_data_contributor_id=setup[1].id)
    session.add(request)
    session.commit()

    message = create_message(session, sender_id=user_id, request_id=request.id, body="test_message_create_duplicate")
    message = create_message(session, sender_id=user_id, request_id=request.id, body="test_message_create_duplicate")    

def test_message_get_by_sender_id(session, setup, register_user):
    user_id, user_email = register_user(email=f"user_1@test_message_get_by_sender_id.com", name="test_message_get_by_sender_id")
    user_id_2, user_email_2 = register_user(email=f"user_2@test_message_get_by_sender_id.com", name="test_message_get_by_sender_id")
    request = Request(project_id=setup[0].id, consortium_data_contributor_id=setup[1].id)
    session.add(request)
    session.commit()

    message = create_message(session, sender_id=user_id, request_id=request.id, body="test_message_get_by_sender_id")
    message_2 = create_message(session, sender_id=user_id_2, request_id=request.id, body="test_message_get_by_sender_id")

    messages = get_messages(session, sender_id=user_id)
    assert len(messages) == 1
    assert messages[0].body == "test_message_get_by_sender_id"

def test_message_get_by_request_id(session, setup, register_user):
    user_id, user_email = register_user(email=f"user_1@test_message_get_by_request_id.com", name="test_message_get_by_request_id")
    request = Request(project_id=setup[0].id, consortium_data_contributor_id=setup[1].id)
    request_2 = Request(project_id=setup[0].id, consortium_data_contributor_id=setup[2].id)
    session.add(request)
    session.commit()

    message = create_message(session, sender_id=user_id, request_id=request.id, body="test_message_get_by_request_id")
    message_2 = create_message(session, sender_id=user_id, request_id=request_2.id, body="test_message_get_by_request_id")

    messages = get_messages(session, request_id=request.id)
    assert len(messages) == 1
    assert messages[0].body == "test_message_get_by_request_id"

def test_message_get_by_sender_id_and_request_id(session, setup, register_user):
    user_id, user_email = register_user(email=f"user_1@test_message_get_by_sender_id_and_request_id.com", name="test_message_get_by_sender_id_and_request_id")
    user_id_2, user_email_2 = register_user(email=f"user_2@test_message_get_by_sender_id_and_request_id.com", name="test_message_get_by_sender_id_and_request_id")
    request = Request(project_id=setup[0].id, consortium_data_contributor_id=setup[1].id)
    request_2 = Request(project_id=setup[0].id, consortium_data_contributor_id=setup[2].id)
    session.add(request)
    session.commit()

    message = create_message(session, sender_id=user_id, request_id=request.id, body="test_message_get_by_sender_id_and_request_id")
    message_2 = create_message(session, sender_id=user_id, request_id=request_2.id, body="test_message_get_by_sender_id_and_request_id")
    message_3 = create_message(session, sender_id=user_id_2, request_id=request.id, body="test_message_get_by_sender_id_and_request_id")
    message_4 = create_message(session, sender_id=user_id_2, request_id=request_2.id, body="test_message_get_by_sender_id_and_request_id")

    messages = get_messages(session, sender_id=user_id, request_id=request.id)
    assert len(messages) == 1
    assert messages[0].body == "test_message_get_by_sender_id_and_request_id"


def test_message_get_throw_not_found(session, setup, register_user):
    user_id, user_email = register_user(email=f"user_1@test_message_get_throw_not_found.com", name="test_message_get_throw_not_found")
    request = Request(project_id=setup[0].id, consortium_data_contributor_id=setup[1].id)
    session.add(request)
    session.commit()
    with pytest.raises(NotFound):
        messages = get_messages(session, sender_id=user_id, throw_not_found=True)

def test_message_get_many_is_false(session, setup, register_user):
    user_id, user_email = register_user(email=f"user_1@test_message_get_many_is_false.com", name="test_message_get_many_is_false")
    request = Request(project_id=setup[0].id, consortium_data_contributor_id=setup[1].id)
    request_2 = Request(project_id=setup[0].id, consortium_data_contributor_id=setup[2].id)
    session.add(request)
    session.commit()

    message = create_message(session, sender_id=user_id, request_id=request.id, body="test_message_get_many_is_false")
    message_2 = create_message(session, sender_id=user_id, request_id=request_2.id, body="test_message_get_many_is_false")

    with pytest.raises(UserError): 
        messages = get_messages(session, sender_id=user_id, many=False)

