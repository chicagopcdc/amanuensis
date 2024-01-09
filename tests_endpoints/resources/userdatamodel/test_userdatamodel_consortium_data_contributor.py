from amanuensis.models import ConsortiumDataContributor
from amanuensis.resources.userdatamodel import create_consortium, get_consotium_by_code
import pytest


@pytest.fixture(scope="function")
def consortiums(session):

    consortium = ConsortiumDataContributor(
        code="TEST",
        name="TEST"
    )

    session.add(consortium)
    session.commit

    yield consortium

    session.query(ConsortiumDataContributor).filter(ConsortiumDataContributor.code == "TEST").delete()
    session.commit()

def test_create_consortium(session):
    data = create_consortium(session, "TEST", "TEST")
    test_data = session.query(ConsortiumDataContributor).filter(ConsortiumDataContributor.code == "TEST").first()

    assert data.id == test_data.id

    session.query(ConsortiumDataContributor).filter(ConsortiumDataContributor.code == "TEST").delete()
    session.commit()

def test_get_consortium_by_code(session, consortiums):
    data = get_consotium_by_code(session, consortiums.code)
    assert data.code == "TEST"


