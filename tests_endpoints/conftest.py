import pytest
from mock import patch, MagicMock
from amanuensis import app, app_init
from amanuensis.models import *
from userportaldatamodel.models import ProjectSearch
import requests


app_init(app, config_file_name="amanuensis-config.yaml")

@pytest.fixture(scope="session")
def app_instance():
    with app.app_context():
        yield app

@pytest.fixture(scope="session")
def client(app_instance):
    with app_instance.test_client() as client:
        yield client

@pytest.fixture(scope="session")
def session(app_instance):
    with app_instance.app_context():

        session = app_instance.scoped_session
        
        session.query(RequestState).delete()
        session.query(SearchIsShared).delete()
        session.query(ProjectAssociatedUser).delete()
        session.query(ProjectSearch).delete()
        session.query(AssociatedUser).delete()
        session.query(Request).delete()
        session.query(Project).delete()
        session.query(ConsortiumDataContributor).filter(ConsortiumDataContributor.code == "ENDPOINT_TEST").delete()
        session.query(ConsortiumDataContributor).filter(ConsortiumDataContributor.code == "TEST").delete()
        session.query(ConsortiumDataContributor).filter(ConsortiumDataContributor.code == "TEST1").delete()
        session.query(ConsortiumDataContributor).filter(ConsortiumDataContributor.code == "TEST2").delete()
        session.query(ConsortiumDataContributor).filter(ConsortiumDataContributor.code == "TEST3").delete()
        session.query(ConsortiumDataContributor).filter(ConsortiumDataContributor.code == "FAKE_CONSORTIUM_1").delete()
        session.query(ConsortiumDataContributor).filter(ConsortiumDataContributor.code == "FAKE_CONSORTIUM_2").delete()
        session.query(ConsortiumDataContributor).filter(ConsortiumDataContributor.code == "BAD").delete()
        session.query(State).filter(State.code == "STATE1").delete()
        session.query(State).filter(State.code == "STATE2").delete()
        session.query(AssociatedUserRoles).filter(AssociatedUserRoles.code == "TEST").delete()
        session.query(Search).delete()

        session.commit()

        yield session
    

# Add a finalizer to ensure proper teardown
@pytest.fixture(scope="session", autouse=True)
def teardown(request, app_instance, session):
    def cleanup():
        session.remove()
        # Explicitly pop the app context to avoid the IndexError
        #app_instance.app_context().pop()

    request.addfinalizer(cleanup)

