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
    
import pytest
from mock import patch, Mock
from cdislogging import get_logger


logger = get_logger(logger_name=__name__)

@pytest.fixture(scope='function')
def patch_boto(app_instance):
    with patch.object(app_instance.boto, "presigned_url", return_value="aws_url_to_data"):
        yield

@pytest.fixture(scope="session", autouse=True)
def fence_users():
    yield []

@pytest.fixture(scope="session", autouse=True)
def add_user_to_fence(fence_users):
    

    def add(email, name, role="user"):

        user_id = fence_users[-1]["id"] + 1 if fence_users else 1
    
        user = {
            "first_name": f"{name}_first_{user_id}",
            "id": user_id,
            "institution": f"{name}_university",
            "last_auth": "Fri, 19 Jan 2024 20:33:37 GMT",
            "last_name": f"{name}_last_{user_id}",
            "name": email,
            "role": role
        }

        fence_users.append(user)

        return user["id"], user["name"]
    
    yield add

@pytest.fixture(scope="session", autouse=True)
def fence_get_users_mock(fence_users):
    '''
    amanuensis sends a request to fence for a list of user ids 
    matching the supplied list of user email addresses
    '''
    def fence_get_users(config=None, usernames=None, ids=None):
        if (ids and usernames):
            logger.error("fence_get_users: Wrong params, only one among `ids` and `usernames` should be set.")
            return {}


        if usernames:
            queryBody = {
                'usernames': usernames
            }
        elif ids:
            queryBody = {
                'ids': ids
            }
        else:
            logger.error("fence_get_users: Wrong params, at least one among `ids` and `usernames` should be set.")
            return {}
        return_users = {"users": []}
        for user in fence_users:
            if 'ids' in queryBody:
                if user['id'] in queryBody['ids']:
                    return_users['users'].append(user)
            else:
                if user['name'] in queryBody['usernames']:
                    return_users['users'].append(user)
        return return_users
    
    yield fence_get_users

@pytest.fixture(scope="session", autouse=True)
def patch_auth_request(app_instance, fence_get_users_mock):
    # Mock the auth_request method to always return True
    def mock_auth_request(jwt, service=None, methods=None, resources=None):
        fence_user = fence_get_users_mock(ids=[int(jwt)])["users"]
        if len(fence_user) == 1 and fence_user[0]["role"] == "admin":
            return True
        else:
            return False
    with patch.object(app_instance.arborist, 'auth_request', side_effect=mock_auth_request):
        yield


# Add a finalizer to ensure proper teardown
@pytest.fixture(scope="session", autouse=True)
def teardown(request, app_instance, session):
    def cleanup():
        session.remove()
        # Explicitly pop the app context to avoid the IndexError
        #app_instance.app_context().pop()

    request.addfinalizer(cleanup)

