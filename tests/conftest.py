import pytest
from mock import patch, MagicMock
from amanuensis import app, app_init
from amanuensis.models import *
from userportaldatamodel.models import ProjectSearch
import requests
from amanuensis.config import config
from cdislogging import get_logger
from pcdcutils.signature import SignatureManager
import json
from amanuensis.errors import AuthError
app_init(app, config_file_name="amanuensis-config.yaml")

logger = get_logger(logger_name=__name__)
from amanuensis.models import ConsortiumDataContributor

@pytest.fixture(scope="session")
def app_instance():
    with app.app_context():
        yield app

@pytest.fixture(scope="session")
def client(app_instance):
    with app_instance.test_client() as client:
        yield client

@pytest.fixture(scope="session", autouse=True)
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
        session.query(ConsortiumDataContributor).delete()
        consortiums = []
        consortiums.append(
            ConsortiumDataContributor(
                name="INRG", 
                code ="INRG"
            )
        )
        consortiums.append(
                ConsortiumDataContributor(
                    name="INSTRUCT", 
                    code ="INSTRUCT"
                    )
        )
        consortiums.append(
            ConsortiumDataContributor(
                name="INTERACT",
                code ="INTERACT"
            )
        )

        session.add_all(consortiums)
        session.query(State).filter(State.code == "STATE1").delete()
        session.query(State).filter(State.code == "STATE2").delete()
        session.query(State).filter(State.code == "ENDPOINT_TEST").delete()
        session.query(AssociatedUserRoles).filter(AssociatedUserRoles.code == "TEST").delete()
        session.query(Search).delete()

        session.commit()

        yield session

        session.commit()
    

@pytest.fixture(scope='function')
def patch_boto(app_instance):
    # Create the patch object
    patch_obj = patch.object(app_instance.boto, "presigned_url", return_value="aws_url_to_data")
    # Start the patch
    patch_context = patch_obj.start()
    
    # Yield the patch object if you want to use it in the test
    yield patch_context

    # Stop the patch after the test finishes
    patch_obj.stop()

@pytest.fixture(scope="session", autouse=True)
def mock_signature_manager():
    config["RSA_PRIVATE_KEY"] = "mock_private_key"
    with patch("amanuensis.resources.fence.SignatureManager") as mock_sm:
        mock_sm.return_value.sign.return_value = b"mock_signature"
        yield

@pytest.fixture(scope="session", autouse=True)
def fence_users():
    yield []

@pytest.fixture(scope="session", autouse=True)
def register_user(fence_users):
    

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
def find_fence_user(fence_users):
    def get_fence_user(queryBody):
        if isinstance(queryBody, str):
            queryBody = json.loads(queryBody)
        return_users = {"users": []}
        print(queryBody)
        for user in fence_users:
            if 'ids' in queryBody:
                if user['id'] in queryBody['ids']:
                    return_users['users'].append(user)
            else:
                if user['name'] in queryBody['usernames']:
                    return_users['users'].append(user)
        print(return_users)
        return return_users
    yield get_fence_user

@pytest.fixture(scope="session", autouse=True)
def patch_auth_request(app_instance, find_fence_user):
    # Mock the auth_request method to always return True
    def mock_auth_request(jwt, service=None, methods=None, resources=None):
        fence_user = find_fence_user({"ids": [int(jwt)]})["users"]
        if len(fence_user) == 1 and fence_user[0]["role"] == "admin":
            return True
        else:
            return False
    with patch.object(app_instance.arborist, 'auth_request', side_effect=mock_auth_request):
        yield


@pytest.fixture(scope="function")
def mock_requests_post(request, find_fence_user):


    def do_patch(consortiums=None, urls={}):
        
        def response_for(url, *args, **kwargs):
            nonlocal urls
            default_urls = {config["GET_CONSORTIUMS_URL"]: 200, "http://fence-service/admin/users/selected": 200}
            default_urls.update(urls)
            urls = default_urls

            mocked_response = MagicMock(requests.post)

            if url not in urls:
                mocked_response.status_code = 404
                mocked_response.text = "NOT FOUND"

            elif 'data' not in kwargs or urls[url] == 400:
                mocked_response.status_code = 400
                mocked_response.json = MagicMock(return_value="BAD REQUEST")
            
            elif urls[url] == 403:
                mocked_response.status_code = 403
                mocked_response.text = "FORBIDDEN"

            
            else:
                if isinstance(kwargs["data"], str):
                    data = json.loads(kwargs["data"]) 
                if 'ids' in data or 'usernames' in data:
                    content = find_fence_user(kwargs['data'])
                else:
                    content = consortiums
              
                mocked_response.json = MagicMock(return_value=content)

                code = 200
                mocked_response.status_code = code

            return mocked_response
        
        patch_method = patch.multiple(
            "amanuensis.resources.consortium_data_contributor.requests",  # Patching requests in the consortium module
            "amanuensis.resources.fence.requests",  # Patching requests in the fence module
            post=MagicMock(side_effect=response_for)  # Both patches share the same side_effect
        )

        patch_method.start()

        request.addfinalizer(patch_method.stop)
    
    return do_patch


@pytest.fixture(scope="function")
def login(request, find_fence_user):
    def patch_user(id, username):
        fence_user = find_fence_user({"ids": [id]})["users"]
        if not fence_user:
            raise AuthError("The user id {} does not exist in the commons".format(id))
        else:
            id = fence_user[0]["id"]
            username = fence_user[0]["name"]
        # Patch `current_user` in both modules: filterset and admin
        patcher_filterset = patch('amanuensis.blueprints.filterset.current_user')
        patcher_admin = patch('amanuensis.blueprints.admin.current_user')
        patcher_download_urls = patch('amanuensis.blueprints.download_urls.current_user')
        patcher_projects = patch('amanuensis.blueprints.project.current_user')

        # Start both patches and set their attributes
        mock_current_user_filterset = patcher_filterset.start()
        mock_current_user_admin = patcher_admin.start()
        mock_current_user_download_urls = patcher_download_urls.start()
        mock_current_user_projects = patcher_projects.start()

        # Set the same `id` and `username` for both mock objects
        mock_current_user_filterset.id = id
        mock_current_user_filterset.username = username

        mock_current_user_download_urls.id = id
        mock_current_user_download_urls.username = username

        mock_current_user_admin.id = id
        mock_current_user_admin.username = username

        mock_current_user_projects.id = id
        mock_current_user_projects.username = username

        request.addfinalizer(patcher_filterset.stop)
        request.addfinalizer(patcher_admin.stop)
        request.addfinalizer(patcher_download_urls.stop)
        request.addfinalizer(patcher_projects.stop)

    
    return patch_user

@pytest.fixture(scope="module", autouse=True)
def s3(app_instance):
    try: 

        s3 = app_instance.boto.s3_client
        bucket_name = 'amanuensis-upload-file-test-bucket'

        # Check if the bucket exists
        def bucket_exists(bucket_name):
            response = s3.list_buckets()
            for bucket in response['Buckets']:
                if bucket['Name'] == bucket_name:
                    return True
            return False

        # Create bucket if it doesn't exist
        if not bucket_exists(bucket_name):
            s3.create_bucket(Bucket=bucket_name)
            logger.info(f"Bucket '{bucket_name}' created.")

        # Delete file if it exists
        try:
            s3.delete_object(Bucket=bucket_name, Key='data_1')
            logger.info("File 'data_1' deleted.")
        except s3.exceptions.NoSuchKey:
            logger.info("File 'data_1' does not exist.")

    
    except Exception as e:
        logger.error(f"Failed to set up s3 bucket, tests will fail {e}")
        yield None

    yield s3

    response = s3.list_objects_v2(Bucket=bucket_name)
    if 'Contents' in response:
        for obj in response['Contents']:
            s3.delete_object(Bucket=bucket_name, Key=obj['Key'])
            logger.info(f"deleted {obj['Key']}")
    
    s3.delete_bucket(Bucket=bucket_name)
    logger.info(f"delete bucket {bucket_name}")

# Add a finalizer to ensure proper teardown
@pytest.fixture(scope="session", autouse=True)
def teardown(request, app_instance, session):
    def cleanup():
        session.remove()
        # Explicitly pop the app context to avoid the IndexError
        #app_instance.app_context().pop()

    request.addfinalizer(cleanup)


