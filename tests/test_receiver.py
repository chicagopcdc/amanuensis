import pytest
from amanuensis.models import Receiver, Message, Project, Request, ConsortiumDataContributor
from amanuensis.resources.userdatamodel.receivers import create_receiver

@pytest.fixture(scope="module", autouse=True)
def setup(session):
    project = Project(name="test_receiver_project_helper")
    session.add(project)

    INRG = session.query(ConsortiumDataContributor).filter(ConsortiumDataContributor.code == "INRG").first()
    INSTRUCT = session.query(ConsortiumDataContributor).filter(ConsortiumDataContributor.code == "INSTRUCT").first()
    INTERACT = session.query(ConsortiumDataContributor).filter(ConsortiumDataContributor.code == "INTERACT").first()

    session.commit()

    yield [project, INRG, INSTRUCT, INTERACT]


def test_create_receiver_helper(session, setup, register_user):
    user_id, user_email = register_user(email=f"user_1@test_receiver_create.com", name="test_receiver_create")
    request = Request(project_id=setup[0].id, consortium_data_contributor_id=setup[1].id)
    session.add(request)
    session.commit()

    message = Message(sender_id=user_id, request_id=request.id, body="test_receiver_create")
    session.add(message)
    session.commit()

    receiver = create_receiver(session, receiver_id=user_id, message_id=message.id)
    assert receiver.receiver_id == user_id
    assert receiver.message_id == message.id    

    assert session.query(Receiver).filter(Receiver.receiver_id == user_id and Receiver.message_id == message.id).first() is not None


def test_create_duplicate_receiver(session, setup, register_user):
    user_id, user_email = register_user(email=f"user_1@test_receiver_create_duplicate.com", name="test_receiver_create_duplicate")
    request = Request(project_id=setup[0].id, consortium_data_contributor_id=setup[1].id)
    session.add(request)
    session.commit()

    message = Message(sender_id=user_id, request_id=request.id, body="test_receiver_create_duplicate")
    session.add(message)
    session.commit()

    receiver = create_receiver(session, receiver_id=user_id, message_id=message.id)
    assert receiver.receiver_id == user_id
    assert receiver.message_id == message.id    

    receiver = create_receiver(session, receiver_id=user_id, message_id=message.id)
    assert receiver.receiver_id == user_id
    assert receiver.message_id == message.id    

    assert session.query(Receiver).filter(Receiver.receiver_id == user_id and Receiver.message_id == message.id).count() == 2