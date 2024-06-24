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
    yield [
        {
            "first_name": "endpoint_user_1",
            "id": 101,
            "institution": "test university",
            "last_auth": "Fri, 19 Jan 2024 20:33:37 GMT",
            "last_name": "endpoint_user_last_1",
            "name": "endpoint_user_1@test.com",
            "role": "user"
        },
        {
            "first_name": "endpoint_user_2",
            "id": 102,
            "institution": "test university",
            "last_auth": "Fri, 19 Jan 2024 20:33:37 GMT",
            "last_name": "endpoint_user_last",
            "name": "endpoint_user_2@test.com",
            "role": "user"
        },
        {
            "first_name": "endpoint_user_3",
            "id": 103,
            "institution": "test university",
            "last_auth": "Fri, 19 Jan 2024 20:33:37 GMT",
            "last_name": "endpoint_user_last_3",
            "name": "endpoint_user_3@test.com",
            "role": "user"
        },
        {
            "first_name": "admin_first",
            "id": 200,
            "institution": "uchicago",
            "last_auth": "Fri, 20 Jan 2024 20:33:37 GMT",
            "last_name": "admin_last",
            "name": "admin@uchicago.edu",
            "role": "admin"
        },
        {
            "first_name": "endpoint_user_6",
            "id": 106,
            "institution": "test university",
            "last_auth": "Fri, 19 Jan 2024 20:33:37 GMT",
            "last_name": "endpoint_user_last_6",
            "name": "endpoint_user_6@test.com",
            "role": "user"
        },
        {
            "first_name": "endpoint_user_7",
            "id": 107,
            "institution": "test university",
            "last_auth": "Fri, 19 Jan 2024 20:33:37 GMT",
            "last_name": "endpoint_user_last_7",
            "name": "endpoint_user_7@test.com",
            "role": "user"
        }
        ,
        {
            "first_name": "endpoint_user_8",
            "id": 108,
            "institution": "test university",
            "last_auth": "Fri, 19 Jan 2024 20:33:37 GMT",
            "last_name": "endpoint_user_last_8",
            "name": "endpoint_user_8@test.com",
            "role": "user"
        }
    ]

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