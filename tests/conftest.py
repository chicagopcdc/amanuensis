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
from sqlalchemy import or_, and_, text
from amanuensis.errors import AuthError
from amanuensis.resources.request import calculate_overall_project_state
from amanuensis.models import ConsortiumDataContributor
from flask import request
from sqlalchemy import func

logger = get_logger(logger_name=__name__)

def pytest_addoption(parser):
    parser.addoption(
        "--configuration-file",  # The CLI argument
        action="store",   # Stores the value passed to this argument
        default="amanuensis-config.yaml",  # The default value
        help="Path to the config file"
    )
    parser.addoption(
        "--test-emails-to-send-notifications",  # The CLI argument
        action="store",   # Stores the value passed to this argument
        default=[],
        help="The email addresses to send notifications to for AWS SES"
    )

@pytest.fixture(scope="session", autouse=True)
def initiate_app(pytestconfig):
    app_init(app, config_file_name=pytestconfig.getoption("--configuration-file"))

@pytest.fixture(scope="session")
def app_instance(initiate_app):
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
        session.query(Receiver).delete()
        session.query(Message).delete()
        session.query(SearchIsShared).delete()
        session.query(ProjectAssociatedUser).delete()
        session.query(ProjectSearch).delete()
        session.query(AssociatedUser).delete()
        session.query(Receiver).delete()
        session.query(Message).delete()
        session.query(Request).delete()
        session.query(ProjectDataPoints).delete()
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
        session.query(Notification).delete()
        session.query(NotificationLog).delete()
        
        session.commit()

        yield session

        session.commit()
    

@pytest.fixture(scope='function')
def patch_s3_client(request, app_instance):
    def do_patch(return_value="This_is_a_presigned_url"):
        # Create the patch object
        patch_obj = patch.object(app_instance.boto, "presigned_url", return_value=return_value)
        # Start the patch
        patch_context = patch_obj.start()
        
        # Add a finalizer to stop the patch
        request.addfinalizer(patch_obj.stop)
    
    return do_patch

@pytest.fixture(scope='function')
def patch_ses_client(request, app_instance):
    def do_patch(return_value="this_is_an_email_response"):
        # Create the patch object
        patch_obj = patch.object(app_instance.ses_boto, "send_email", return_value=return_value)
        # Start the patch
        patch_obj.start()
        
        # Add a finalizer to stop the patch
        request.addfinalizer(patch_obj.stop)
    
    return do_patch

@pytest.fixture(scope="session", autouse=True)
def mock_signature_manager():
    config["RSA_PRIVATE_KEY"] = "mock_private_key"
    with patch("amanuensis.resources.fence.Gen3RequestManager") as mock_sm:
        mock_sm.return_value.make_gen3_signature.return_value = "mock_signature"
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
            "username": email,
            "role": role
        }

        fence_users.append(user)

        return user["id"], user["username"]
    
    yield add


@pytest.fixture(scope="session", autouse=True)
def find_fence_user(fence_users):
    def get_fence_user(queryBody):
        if isinstance(queryBody, str):
            queryBody = json.loads(queryBody)
        return_users = {"users": []}
        for user in fence_users:
            if 'ids' in queryBody:
                if user['id'] in queryBody['ids']:
                    return_users['users'].append(user)
            else:
                if user['username'] in queryBody['usernames']:
                    return_users['users'].append(user)
        return return_users
    yield get_fence_user



@pytest.fixture(scope="function")
def patch_auth_header(monkeypatch):
    def _patch_auth_header(auth_header_value):
        monkeypatch.setattr(
            "amanuensis.resources.fence.get_jwt_from_header",
            lambda: auth_header_value
        )
    return _patch_auth_header


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
            default_urls = {config["GET_CONSORTIUMS_URL"]: 200, f"{config['FENCE']}/admin/users/selected": 200}
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
def mock_requests_get(request, fence_users):


    def do_patch(urls={}):
        
        def response_for(url, *args, **kwargs):
            nonlocal urls
            default_urls = {f"{config['FENCE']}/admin/users": 200}
            default_urls.update(urls)
            urls = default_urls
            print(urls)

            mocked_response = MagicMock(requests.get)

            if url not in urls:
                mocked_response.status_code = 404
                mocked_response.text = "NOT FOUND"

            elif urls[url] == 400:
                mocked_response.status_code = 400
                mocked_response.json = MagicMock(return_value="BAD REQUEST")
            
            elif urls[url] == 401:
                print("here")
                mocked_response.status_code = 401
                mocked_response.text = "UNAUTHORIZED"
            
            elif urls[url] == 403:
                mocked_response.status_code = 403
                mocked_response.text = "FORBIDDEN"
                mocked_response.json = MagicMock(return_value={})
            
            else:
                mocked_response.json = MagicMock(return_value={"users": fence_users})
                code = 200
                mocked_response.status_code = code

            return mocked_response
        
        patch_method = patch.multiple(
            "amanuensis.resources.fence.requests",  # Patching requests in the fence module
            get=MagicMock(side_effect=response_for)  # Both patches share the same side_effect
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
            username = fence_user[0]["username"]
        # Patch `current_user` in both modules: filterset and admin
        patcher_filterset = patch('amanuensis.blueprints.filterset.current_user')
        patcher_admin = patch('amanuensis.blueprints.admin.current_user')
        patcher_download_urls = patch('amanuensis.blueprints.download_urls.current_user')
        patcher_projects = patch('amanuensis.blueprints.project.current_user')
        patcher_notifications = patch('amanuensis.blueprints.notification.current_user')

        # Start both patches and set their attributes
        mock_current_user_filterset = patcher_filterset.start()
        mock_current_user_admin = patcher_admin.start()
        mock_current_user_download_urls = patcher_download_urls.start()
        mock_current_user_projects = patcher_projects.start()
        mock_current_user_notifications = patcher_notifications.start()

        # Set the same `id` and `username` for both mock objects
        mock_current_user_filterset.id = id
        mock_current_user_filterset.username = username

        mock_current_user_download_urls.id = id
        mock_current_user_download_urls.username = username

        mock_current_user_admin.id = id
        mock_current_user_admin.username = username

        mock_current_user_projects.id = id
        mock_current_user_projects.username = username

        mock_current_user_notifications.id = id
        mock_current_user_notifications.username = username

        request.addfinalizer(patcher_filterset.stop)
        request.addfinalizer(patcher_admin.stop)
        request.addfinalizer(patcher_download_urls.stop)
        request.addfinalizer(patcher_projects.stop)
        request.addfinalizer(patcher_notifications.stop)

    
    return patch_user

@pytest.fixture(scope="module", autouse=True)
def s3(app_instance):

    s3 = None

    try: 

        s3 = app_instance.s3_boto.s3_client
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

    yield s3
    if s3:
        response = s3.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in response:
            for obj in response['Contents']:
                s3.delete_object(Bucket=bucket_name, Key=obj['Key'])
                logger.info(f"deleted {obj['Key']}")
        
        s3.delete_bucket(Bucket=bucket_name)
        logger.info(f"delete bucket {bucket_name}")

# Helper fixtures to make tests easier to follow along with and create
# these should handle calling the server 
#then validate the DB that the data was correctly stored

@pytest.fixture(scope="session", autouse=True)
def project_get(client):

    def route_project_get(authorization_token, 
                          special_user_admin=False, 
                          status_code=200
                          ):
        
        url = "/projects" + ("?special_user=admin" if special_user_admin else "")
        response = client.get(url, headers={"Authorization": f'bearer {authorization_token}'})

        assert response.status_code == status_code
        #here we should validate based on the DB and inputs that the response is correct 
        return response

    yield route_project_get

@pytest.fixture(scope="function")
def project_post(session, client, mock_requests_post, find_fence_user):

    def route_project_post(authorization_token,
                           consortiums_to_be_returned_from_pcdc_analysis_tools=[],
                           associated_users_emails=[],
                           name="",
                           description=None,
                           institution=None,
                           filter_set_ids=None,
                           explorer_id=None,
                           status_code=200):
        
        mock_requests_post(consortiums=consortiums_to_be_returned_from_pcdc_analysis_tools)

        current_users = session.query(AssociatedUser).filter(
                or_(AssociatedUser.user_id == authorization_token,
                    AssociatedUser.email.in_(associated_users_emails))
            ).all()

        current_filters = session.query(Search).filter(
                                Search.id.in_(filter_set_ids)
                         ).all()        
        
        
        json = {}
        if associated_users_emails is not None:
            json["associated_users_emails"] = associated_users_emails
        if name:
            json["name"] = name
        if description is not None:
            json["description"] = description
        if institution is not None:
            json["institution"] = institution
        if filter_set_ids is not None:
            json["filter_set_ids"] = filter_set_ids
        if explorer_id is not None:
            json["explorer_id"] = explorer_id

        response = client.post("/projects", json=json, headers={"Authorization": f'bearer {authorization_token}'})

        assert response.status_code == status_code

        project_id = response.json.get("id") if response.status_code == 200 else None

        project = session.query(Project).filter(Project.id == project_id).first()
        
        #fetch data for new filter sets and project filter sets

        new_filter_sets = session.query(Search).filter(
                            Search.name.in_(
                                [name + "_" + user_gen_filter.name for user_gen_filter in current_filters]
                            )
                        ).all()
        
        project_filter_sets = session.query(ProjectSearch).filter(
                            ProjectSearch.project_id == project_id
                        ).all()
        
        #fetch data for new requests and states

        project_requests = session.query(Request).filter(
                            Request.project_id == project_id
                        ).all()
        
        project_requests_states = session.query(RequestState).filter(
                                    RequestState.request_id.in_(
                                        [request.id for request in project_requests]
                                    )
                                ).all()

        #fetch data for new associated users and project associated users

        project_associated_users = session.query(ProjectAssociatedUser).filter(
                            ProjectAssociatedUser.project_id == project_id
                        ).all()
        
        updated_associated_users = session.query(AssociatedUser).filter(
                            or_(
                                AssociatedUser.user_id == authorization_token,
                                AssociatedUser.email.in_(associated_users_emails)
                            )
                        ).all()
        
        if status_code == 200:

            assert project.name == name
            assert project.first_name == None
            assert project.last_name == None
            assert project.user_id == authorization_token
            assert project.user_source == "fence"
            assert project.institution == institution
            assert project.description == description
            assert project.approved_url == None
            assert project.active == True

            #check filter-sets and searches connected to the project

            assert len(new_filter_sets) == len(current_filters)

            for new_filter_set in new_filter_sets:
                
                #get the filter set created by the user
                #the test suite will just assume that all the filters have unique names to make this easier
                user_gen_filter = [user_gen_filter for user_gen_filter in current_filters if user_gen_filter.name in new_filter_set.name][0]


                assert new_filter_set.user_id == None
                assert new_filter_set.user_source == ""
                assert new_filter_set.name == project.name + "_" + user_gen_filter.name
                assert new_filter_set.description == user_gen_filter.description
                assert new_filter_set.filter_object == user_gen_filter.filter_object
                assert new_filter_set.filter_source == "manual"
                assert new_filter_set.filter_source_internal_id == user_gen_filter.filter_source_internal_id
                assert new_filter_set.ids_list == user_gen_filter.ids_list
                assert new_filter_set.graphql_object == user_gen_filter.graphql_object
                assert new_filter_set.es_index == user_gen_filter.es_index
                assert new_filter_set.dataset_version == user_gen_filter.dataset_version
                assert new_filter_set.is_superseded_by == user_gen_filter.is_superseded_by
                assert new_filter_set.active == True
                assert new_filter_set.is_valid == True

            assert [filter_set.search_id for filter_set in project_filter_sets] == [search.id for search in new_filter_sets]


            #check requests their consortiums and states

            assert sorted([request.consortium_data_contributor.code for request in project_requests]) == sorted(consortiums_to_be_returned_from_pcdc_analysis_tools)

            assert len(project_requests_states) == len(project_requests)
            assert any(request_state.state.code == "IN_REVIEW" for request_state in project_requests_states)


            #check associated users and project associated users
            associated_users_in_fence = [find_fence_user({"ids":[authorization_token]})["users"][0]["username"]]
            associated_users_not_in_fence = []

            for associated_user in associated_users_emails:
                fence_user = find_fence_user({"usernames":[associated_user]})["users"]

                if not fence_user:
                    associated_users_not_in_fence.append(associated_user)

                elif fence_user[0]["id"] == authorization_token:
                    continue

                else:
                    associated_users_in_fence.append(fence_user[0]["username"])

            assert len(updated_associated_users) == len(associated_users_in_fence + associated_users_not_in_fence)

            for updated_associated_user in updated_associated_users:

                if not updated_associated_user.user_id:

                    assert updated_associated_user.email in associated_users_not_in_fence
                    assert updated_associated_user.user_source == None
                    assert updated_associated_user.active == False

                else:

                    assert updated_associated_user.email in associated_users_in_fence
                    assert updated_associated_user.user_source == "fence"
                    assert updated_associated_user.active == True

                
                


            assert len(project_associated_users) == len(associated_users_in_fence + associated_users_not_in_fence)
            for project_associated_user in project_associated_users:
                assert project_associated_user.active == True
                assert project_associated_user.project_id == project_id
                assert project_associated_user.role.code == "METADATA_ACCESS"
            

        else:

            assert project == None
            assert new_filter_sets == []
            assert project_filter_sets == []
            assert project_requests == []
            assert project_requests_states == []
            assert project_associated_users == []
            assert len(current_users) == len(updated_associated_users)

        return response
    
    yield route_project_post

@pytest.fixture(scope="session", autouse=True)
def filter_set_post(session, client):

    def route_filter_set_post(authorization_token, 
                             explorer_id=None,
                             name=None,
                             filter_object=None,
                             graphql_object=None,
                             description=None,
                             ids_list=None, 
                             status_code=200
                             ):
        
        json = {}
        if name is not None:
            json["name"] = name
        if filter_object is not None:
            json["filters"] = filter_object
        if graphql_object is not None:
            json["gqlFilter"] = graphql_object
        if description is not None:
            json["description"] = description
        if ids_list is not None:
            json["ids_list"] = ids_list

        url = "/filter-sets" + ("?explorerId=" + str(explorer_id) if explorer_id is not None else "")

        response = client.post(url, json=json, headers={"Authorization": f'bearer {authorization_token}'})

        assert response.status_code == status_code

        filter_set_count = session.query(Search).count()
        
        if status_code == 200:

            filter_set = session.query(Search).filter(Search.id == response.json["id"]).first()

            assert filter_set.name == name
            assert filter_set.filter_object == ({} if filter_object is None else filter_object)
            assert filter_set.graphql_object == ({} if graphql_object is None else graphql_object)
            assert filter_set.description == description
            assert filter_set.filter_source_internal_id == explorer_id if explorer_id is not None else 1
            assert filter_set.ids_list == ids_list
            assert filter_set.filter_source == "explorer"
            assert filter_set.user_id == authorization_token
            assert filter_set.user_source == "fence"
            assert filter_set.es_index == None
            assert filter_set.dataset_version == None
            assert filter_set.is_superseded_by == None
            assert filter_set.active == True
            assert filter_set.is_valid == True
        
        else:

            assert session.query(Search).count() == filter_set_count


        return response
    
    yield route_filter_set_post


@pytest.fixture(scope="session", autouse=True)
def filter_set_put(session, client):
    def route_filter_set_put(authorization_token, 
                             filter_set_id=None,
                             explorer_id=1,
                             name=None,
                             filter_object=None,
                             graphql_object=None,
                             description=None,
                             ids_list=None, 
                             status_code=200
                             ):
        
        json = {}
        if name is not None:
            json["name"] = name
        if filter_object is not None:
            json["filters"] = filter_object
        if graphql_object is not None:
            json["gqlFilter"] = graphql_object
        if description is not None:
            json["description"] = description
        if ids_list is not None:
            json["ids_list"] = ids_list

        filter_set = session.query(Search).filter(Search.id == filter_set_id, Search.user_id == authorization_token, Search.filter_source_internal_id == explorer_id).first()
        filter_set_count = session.query(Search).count()

        
        url = "/filter-sets/" + str(filter_set_id)

        response = client.put(url, json=json, headers={"Authorization": f'bearer {authorization_token}'})

        filter_set_after_url = session.query(Search).filter(Search.id == filter_set_id, Search.user_id == authorization_token).first()
        session.refresh(filter_set_after_url)


        assert response.status_code == status_code
        
        if status_code == 200:
            
            #properties that can change
            assert filter_set_after_url.name == (name if name is not None else filter_set.name)
            assert filter_set_after_url.filter_object == (filter_object if filter_object is not None else filter_set.filter_object)
            assert filter_set_after_url.graphql_object == (graphql_object if graphql_object is not None else filter_set.graphql_object)
            assert filter_set_after_url.description == (description if description is not None else filter_set.description)
            assert filter_set_after_url.is_valid == (True if filter_object is not None or graphql_object is not None else filter_set.is_valid)    

            #properties that should not change
            assert filter_set_after_url.filter_source_internal_id == filter_set.filter_source_internal_id 
            assert filter_set_after_url.ids_list == filter_set_after_url.ids_list
            assert filter_set_after_url.filter_source == filter_set_after_url.filter_source
            assert filter_set_after_url.user_id == authorization_token
            assert filter_set_after_url.user_source == filter_set.user_source
            assert filter_set_after_url.es_index == filter_set.es_index
            assert filter_set_after_url.dataset_version == filter_set.dataset_version
            assert filter_set_after_url.is_superseded_by == filter_set.is_superseded_by
            assert filter_set_after_url.active == True  
            
        
        elif status_code == 404:
            assert filter_set == None
        
        else:

            assert filter_set.id == filter_set_after_url.id
            assert filter_set.name == filter_set_after_url.name
            assert filter_set.filter_object == filter_set_after_url.filter_object
            assert filter_set.graphql_object == filter_set_after_url.graphql_object
            assert filter_set.description == filter_set_after_url.description
            assert filter_set.filter_source_internal_id == filter_set_after_url.filter_source_internal_id
            assert filter_set.ids_list == filter_set_after_url.ids_list
            assert filter_set.filter_source == filter_set_after_url.filter_source
            assert filter_set.user_id == filter_set_after_url.user_id
            assert filter_set.user_source == filter_set_after_url.user_source
            assert filter_set.es_index == filter_set_after_url.es_index
            assert filter_set.dataset_version == filter_set_after_url.dataset_version
            assert filter_set.is_superseded_by == filter_set_after_url.is_superseded_by
            assert filter_set.active == filter_set_after_url.active
            assert filter_set.is_valid == filter_set_after_url.is_valid
        
        
        assert session.query(Search).count() == filter_set_count


        return response
    
    yield route_filter_set_put


@pytest.fixture(scope="session", autouse=True)
def admin_filter_set_post(session, client):

    def route_admin_filter_set_post(authorization_token, 
                             user_id=None,
                             name=None,
                             graphql_object=None,
                             description=None,
                             ids_list=None, 
                             status_code=200
                             ):
        
        json = {}
        if user_id is not None:
            json["user_id"] = user_id
        if name is not None:
            json["name"] = name
        if graphql_object is not None:
            json["filters"] = graphql_object
        if description is not None:
            json["description"] = description
        if ids_list is not None:
            json["ids_list"] = ids_list

        url = "/admin/filter-sets"

        response = client.post(url, json=json, headers={"Authorization": f'bearer {authorization_token}'})

        assert response.status_code == status_code

        total_filter_sets = session.query(Search).count()
        
        if status_code == 200:

            filter_set = session.query(Search).filter(Search.id == response.json["id"]).first()

            assert filter_set.name == name
            assert filter_set.filter_object == {}
            assert filter_set.graphql_object == ({} if not graphql_object else graphql_object)
            assert filter_set.description == description
            assert filter_set.filter_source_internal_id == None
            assert filter_set.ids_list == ids_list
            assert filter_set.filter_source == "manual"
            assert filter_set.user_id == user_id
            assert filter_set.user_source == "fence"
            assert filter_set.es_index == None
            assert filter_set.dataset_version == None
            assert filter_set.is_superseded_by == None
            assert filter_set.active == True    
            assert filter_set.is_valid == True
        
        else:

            assert session.query(Search).count() == total_filter_sets


        return response
    
    yield route_admin_filter_set_post


@pytest.fixture(scope="session", autouse=True)
def admin_copy_search_to_user_post(session, client):

    def route_admin_copy_search_to_user_post(authorization_token, 
                             user_id=None,
                             filter_set_id=None,
                             status_code=200
                             ):
        
        json = {}
        if user_id is not None:
            json["userId"] = user_id
        if filter_set_id is not None:
            json["filtersetId"] = filter_set_id

        url = "/admin/copy-search-to-user"

        total_filter_sets = session.query(Search).count()

        response = client.post(url, json=json, headers={"Authorization": f'bearer {authorization_token}'})

        assert response.status_code == status_code
        
        if status_code == 200:

            original_filter_set = session.query(Search).filter(Search.id == filter_set_id).first()

            filter_set = session.query(Search).filter(Search.id == response.json["id"]).first()

            assert filter_set.name == original_filter_set.name
            assert filter_set.filter_object == original_filter_set.filter_object
            assert filter_set.graphql_object == original_filter_set.graphql_object
            assert filter_set.description == original_filter_set.description
            assert filter_set.filter_source_internal_id == original_filter_set.filter_source_internal_id
            assert filter_set.ids_list == original_filter_set.ids_list
            assert filter_set.filter_source == "manual"
            assert filter_set.user_id == user_id
            assert filter_set.user_source == "fence"
            assert filter_set.es_index == None
            assert filter_set.dataset_version == None
            assert filter_set.is_superseded_by == None
            assert filter_set.active == True    
            assert filter_set.is_valid == True
        
        else:   
            assert session.query(Search).count() == total_filter_sets



        return response
    
    yield route_admin_copy_search_to_user_post

@pytest.fixture(scope="function", autouse=True)
def admin_upload_file(session, client, mock_requests_post):
    def route_admin_upload_file(authorization_token, 
                             key=None,
                             project_id=None,
                             expires=None,
                             status_code=200
                             ):
        
        mock_requests_post()

        url = "/admin/upload-file"
        json = {}
        if key is not None:
            json["key"] = key
        if project_id is not None:
            json["project_id"] = project_id
        if expires is not None:
            json["expires"] = expires

        if project_id:
            project_before_request = session.query(Project).filter(Project.id == project_id).first()
            if project_before_request:
                project_status_before_request = calculate_overall_project_state(session, project_id)["status"]
        
        else:
            project_before_request = None
            project_status_before_request = None

        response = client.post(url, json=json, headers={"Authorization": f'bearer {authorization_token}'})

        assert response.status_code == status_code

        if project_id:
            project_after_request = session.query(Project).filter(Project.id == project_id).first()
            
            if project_after_request:
                session.refresh(project_after_request)
        else:
            project_after_request = None

        if status_code == 200:
            assert project_after_request.approved_url == f'https://{config["AWS_CREDENTIALS"]["DATA_DELIVERY_S3_BUCKET"]["bucket_name"]}.s3.amazonaws.com/{key}' 

            calculate_overall_project_state(session, project_id)["status"] == "DATA_AVAILABLE"


        else:
            if project_before_request:
                assert project_before_request.approved_url == project_after_request.approved_url
                assert project_status_before_request == calculate_overall_project_state(session, project_id)["status"]
            

        return response

    yield route_admin_upload_file

@pytest.fixture(scope="session", autouse=True)
def admin_update_associated_user_role(session, client):
    def route_admin_update_associated_user_role(authorization_token, 
                             user_id=None,
                             email=None,
                             role=None,
                             project_id=None,
                             status_code=200
                             ):
        
        json = {}
        if user_id is not None:
            json["user_id"] = user_id
        if email is not None:
            json["email"] = email
        if project_id is not None:
            json["project_id"] = project_id
        if role is not None:
            json["role"] = role

        url = "/admin/associated_user_role"

        if user_id:
            associated_user_role_before = session.query(ProjectAssociatedUser).filter(
                ProjectAssociatedUser.project_id == project_id
                ).join(
                AssociatedUser, ProjectAssociatedUser.associated_user
                ).filter(
                    AssociatedUser.user_id == user_id
                ).first()
        else:
            associated_user_role_before = session.query(ProjectAssociatedUser).filter(
                ProjectAssociatedUser.project_id == project_id
                ).join(
                AssociatedUser, ProjectAssociatedUser.associated_user
                ).filter(
                    AssociatedUser.email == email
                ).first()
        response = client.put(url, json=json, headers={"Authorization": f'bearer {authorization_token}'})

        assert response.status_code == status_code

        if user_id:
            associated_user_role_after = session.query(ProjectAssociatedUser).filter(
                ProjectAssociatedUser.project_id == project_id
                ).join(
                AssociatedUser, ProjectAssociatedUser.associated_user
                ).filter(
                    AssociatedUser.user_id == user_id
                ).first()
        else:
            associated_user_role_after = session.query(ProjectAssociatedUser).filter(
                ProjectAssociatedUser.project_id == project_id
                ).join(
                AssociatedUser, ProjectAssociatedUser.associated_user
                ).filter(
                    AssociatedUser.email == email
                ).first()
        
        session.refresh(associated_user_role_after)

        print(associated_user_role_after.role.code)
        
        if status_code == 200:
            assert associated_user_role_after.role.code == role
        
        else:
            associated_user_role_before.role.code == associated_user_role_after.role.code
        
        return response
    
    yield route_admin_update_associated_user_role

@pytest.fixture(scope="session", autouse=True)
def filter_set_snapshot_post(session, client):
    def route_filter_set_snapshot_post(authorization_token, 
                             filter_set_id=None,
                             users_list=None,
                             status_code=200
                             ):
        
        json = {}
        if filter_set_id is not None:
            json["filterSetId"] = filter_set_id
        if users_list is not None:
            json["users_list"] = users_list

        url = "/filter-sets/snapshot"

        total_filter_sets = session.query(Search).count()
        total_search_is_shared = session.query(SearchIsShared).count()

        response = client.post(url, json=json, headers={"Authorization": f'bearer {authorization_token}'})

        assert response.status_code == status_code
        
        if status_code == 200:
            original_filter_set = session.query(Search).filter(Search.id == filter_set_id).first()
            new_filter_set = session.query(Search).join(SearchIsShared, and_(
                Search.id == SearchIsShared.search_id,
                SearchIsShared.shareable_token == response.json
            )).first()
            snapshot = session.query(SearchIsShared).filter(SearchIsShared.search_id == new_filter_set.id).first()

            assert new_filter_set.name == original_filter_set.name
            assert new_filter_set.filter_object == original_filter_set.filter_object
            assert new_filter_set.graphql_object == original_filter_set.graphql_object
            assert new_filter_set.description == original_filter_set.description
            assert new_filter_set.filter_source_internal_id == original_filter_set.filter_source_internal_id
            assert new_filter_set.ids_list == original_filter_set.ids_list
            assert new_filter_set.filter_source == "explorer"
            assert new_filter_set.user_id == None
            assert new_filter_set.user_source == "fence"
            assert new_filter_set.es_index == None
            assert new_filter_set.dataset_version == None
            assert new_filter_set.is_superseded_by == None
            assert new_filter_set.active == True    
            assert new_filter_set.is_valid == True

            assert snapshot.search_id == new_filter_set.id
            assert snapshot.user_id == users_list
            assert snapshot.access_role == "READ"
            assert snapshot.shareable_token != None

        
        else:   
            assert session.query(Search).count() == total_filter_sets
            assert session.query(SearchIsShared).count() == total_search_is_shared

        return response
    
    yield route_filter_set_snapshot_post

@pytest.fixture(scope="session", autouse=True)
def filter_set_snapshot_get(session, client):
    def route_filter_set_snapshot_get(authorization_token, 
                             token=None,
                             status_code=200
                             ):
        
        url = "/filter-sets/snapshot/" + token

        response = client.get(url, headers={"Authorization": f'bearer {authorization_token}'})

        assert response.status_code == status_code
        
        if status_code == 200:

            snapshot = session.query(SearchIsShared).filter(SearchIsShared.shareable_token == token).first()

            assert response.json["id"] == snapshot.search_id
            assert response.json["name"] == snapshot.search.name
            assert response.json["explorer_id"] == snapshot.search.filter_source_internal_id
            assert response.json["description"] == snapshot.search.description
            assert response.json["filters"] == snapshot.search.filter_object
        
        return response

    yield route_filter_set_snapshot_get

@pytest.fixture(scope="session", autouse=True)
def admin_filter_set_by_project_id_get(session, client):
    def route_admin_filter_set_get_by_project_id(authorization_token, 
                             project_id=None,
                             status_code=200
                             ):
        
        url = "/admin/project_filter_sets/" + (str(project_id) if project_id is not None else "")

        response = client.get(url, headers={"Authorization": f'bearer {authorization_token}'})

        assert response.status_code == status_code
        
        if status_code == 200:

            project_filter_sets = session.query(ProjectSearch).filter(ProjectSearch.project_id == project_id).all()

            assert len(response.json) == len(project_filter_sets)
            
        
        return response

    yield route_admin_filter_set_get_by_project_id

@pytest.fixture(scope="function", autouse=True)
def admin_copy_search_to_project(session, client, mock_requests_post): 
    def route_admin_copy_search_to_project(authorization_token, 
                             project_id=None,
                             filter_set_id=None,
                             status_code=200,
                             consortiums_to_be_returned_from_pcdc_analysis_tools=[],
                             state_code="IN_REVIEW"
                             ):
        mock_requests_post(consortiums=consortiums_to_be_returned_from_pcdc_analysis_tools)
        json = {}
        if project_id is not None:
            json["projectId"] = project_id
        if filter_set_id is not None:
            json["filtersetId"] = filter_set_id

        url = "/admin/copy-search-to-project"

        response = client.post(url, json=json, headers={"Authorization": f'bearer {authorization_token}'})

        assert response.status_code == status_code
        
        if status_code == 200:

            filter_set_id = [filter_set_id] if isinstance(filter_set_id, int) else filter_set_id

            project = session.query(Project).filter(Project.id == project_id).first()

            assert project

            assert len(filter_set_id) == session.query(ProjectSearch).filter(ProjectSearch.project_id == project.id).count()

            for filter_set_id in filter_set_id:
            
                original_filter_set = session.query(Search).filter(Search.id == filter_set_id).first()
                new_filter_set = session.query(Search).join(ProjectSearch, and_(
                    ProjectSearch.project_id == project_id,
                    Search.name == project.name + "_" + original_filter_set.name
                )).first()

                assert session.query(ProjectSearch).filter(
                    and_(
                        ProjectSearch.project_id == project_id,
                        ProjectSearch.search_id == new_filter_set.id
                    )
                ).first()

                #assert new_filter_set.name == original_filter_set.name
                assert new_filter_set.filter_object == original_filter_set.filter_object
                assert new_filter_set.graphql_object == original_filter_set.graphql_object
                assert new_filter_set.description == original_filter_set.description
                assert new_filter_set.filter_source_internal_id == original_filter_set.filter_source_internal_id
                assert new_filter_set.ids_list == original_filter_set.ids_list
                assert new_filter_set.filter_source == "manual"
                assert new_filter_set.user_id == None
                assert new_filter_set.user_source == ""
                assert new_filter_set.es_index == None
                assert new_filter_set.dataset_version == None
                assert new_filter_set.is_superseded_by == None
                assert new_filter_set.active == True    
                assert new_filter_set.is_valid == True

            requests = session.query(Request).filter(Request.project_id == project_id).all()

            current_consortiums = set(consortiums_to_be_returned_from_pcdc_analysis_tools)

            for request in requests:

                current_state = session.query(RequestState).filter(
                    and_(
                        RequestState.request_id == request.id
                    )
                ).order_by(RequestState.update_date.desc()).first()

                if request.consortium_data_contributor.code in consortiums_to_be_returned_from_pcdc_analysis_tools:
                    assert current_state.state.code == state_code
                    current_consortiums.remove(request.consortium_data_contributor.code)

                else:
                    assert current_state.state.code == "DEPRECATED"
            
            assert not current_consortiums


        return response
    
    yield route_admin_copy_search_to_project

@pytest.fixture(scope="function", autouse=True)
def admin_associated_user_post(session, client, mock_requests_post, find_fence_user):

    def route_admin_associated_user_post(authorization_token, 
                             users=None,
                             role=None,
                             status_code=200
                             ):
        
        mock_requests_post()

        json = {}
        if users is not None:
            json["users"] = users
        if role is not None:
            json["role"] = role

        url = "/admin/associated_user"

        response = client.post(url, json=json, headers={"Authorization": f'bearer {authorization_token}'})

        assert response.status_code == status_code

        if status_code == 200:
            for user in users:
                if "email" in user:
                    associated_user = session.query(AssociatedUser).filter(AssociatedUser.email == user["email"]).first()
                    project_user = session.query(ProjectAssociatedUser).filter(
                        ProjectAssociatedUser.associated_user_id == associated_user.id and
                        ProjectAssociatedUser.project_id == user["project_id"]
                    ).first()
                    fence_user = find_fence_user({"usernames":user["email"]})["users"]
                else:
                    associated_user = session.query(AssociatedUser).filter(AssociatedUser.user_id == user["id"]).first()
                    project_user = session.query(ProjectAssociatedUser).filter(
                        ProjectAssociatedUser.associated_user_id == associated_user.id and
                        ProjectAssociatedUser.project_id == user["project_id"]
                    ).first()
                    fence_user = find_fence_user({"ids":[user["id"]]})["users"]
                
                if "id" in user:
                    assert associated_user.user_id == user["id"]
                
                if "email" in user:
                    assert associated_user.email == user["email"]
                
                if fence_user:
                    assert associated_user.user_id == fence_user[0]["id"]
                    assert associated_user.email == fence_user[0]["username"]
                    assert associated_user.user_source == "fence"
                    assert associated_user.active == True
                else:
                    assert associated_user.user_id == None
                    assert associated_user.email == user["email"]
                    assert associated_user.user_source == None
                    assert associated_user.active == False

                assert project_user.project_id == user["project_id"]
                assert project_user.associated_user_id == associated_user.id
                assert project_user.role.code == role if role else config["ASSOCIATED_USER_ROLE_DEFAULT"]
                assert project_user.active == True
        
        return response


    yield route_admin_associated_user_post


@pytest.fixture(scope="function", autouse=True)
def admin_add_project_datapoints_post(session, client):
    def route_admin_add_project_datapoints_post(authorization_token, 
                             term=None,
                             value_list = None,
                             type = None,
                             project_id = None,
                             status_code=200
                             ):
        json = {}
        if term is not None:
            json["term"] = term
        if value_list is not None:
            json["value_list"] = value_list
        if type is not None:
            json["type"] = type
        if project_id is not None:
            json["project_id"] = project_id

        url = "/project-datapoints/add-datapoints"


        response = client.post(url, json=json, headers={"Authorization": f"bearer {authorization_token}"})
        assert response.status_code == status_code, f"failed in admin_add_project_datapoints_post, status code {response.status_code}, expected status code: {status_code}"

        if response.status_code == 200:
            values = response.get_json()
            
            assert values ["term"] == term if term else True
            assert values ["value_list"] == value_list if value_list else True
            assert values["type"] == type if type else True
            assert values["project_id"] == project_id if project_id else True

        return response

    yield route_admin_add_project_datapoints_post


@pytest.fixture(scope="function", autouse=True)
def admin_modify_project_datapoints_put(session, client):
    def route_admin_modify_project_datapoints_put(authorization_token, 
                             id=None,
                             term=None,
                             value_list=None,
                             project_id=None,
                             type=None,
                             status_code=200
                             ):
        json = {}
        if id is not None:
            json["id"] = id
        if term is not None:
            json["term"] = term
        if value_list is not None:
            json["value_list"] = value_list
        if type is not None:
            json["type"] = type
        if project_id is not None:
            json["project_id"] = project_id

        url = "/project-datapoints/modify-datapoints"

        response = client.put(url, json=json, headers={"Authorization": f"bearer {authorization_token}"})

        assert response.status_code == status_code
        if response.status_code == 200:
            values = response.get_json()
            
            assert values["id"] == id if id else True
            assert values ["term"] == term if term else True
            assert values ["value_list"] == value_list if value_list else True
            assert values["type"] == type if type else True
            assert values["project_id"] == project_id if project_id else True
        return response

    yield route_admin_modify_project_datapoints_put


@pytest.fixture(scope="function", autouse=True)
def admin_delete_project_datapoints_delete(session, client):
    def route_admin_delete_project_datapoints_delete(authorization_token, 
                             id=None,
                             status_code=200
                             ):
        json = {}
        if id is not None:
            json["id"] = id

        url = "/project-datapoints/delete-datapoints"

        response = client.delete(url, json=json, headers={"Authorization": f'bearer {authorization_token}'})

        assert response.status_code == status_code
        if response.status_code == 200:
            assert response.get_json()["active"] == False
        return response
    yield route_admin_delete_project_datapoints_delete


@pytest.fixture(scope="function", autouse=True)
def admin_get_project_datapoints_get(session, client):
    def route_admin_get_project_datapoints_get(authorization_token, 
                             term=None,
                             id=None,
                             project_id=None,
                             type=None,
                             many=False,
                             status_code=200
                             ):
        json = {}
        if id is not None:
            json["id"] = id
        if term is not None:
            json["term"] = term
        if type is not None:
            json["type"] = type
        if project_id is not None:
            json["project_id"] = project_id
        if many is not None:
            json["many"] = many
        url = "/project-datapoints/get-datapoints"

        response = client.get(url, json=json, headers={"Authorization": f'bearer {authorization_token}'})
        assert response.status_code == status_code
        if response.status_code == 200:
            values = response.get_json()[0] if many else response.get_json()

            assert values["id"] == id if id else True
            assert values ["term"] == term if term else True
            assert values["type"] == type if type else True
            assert values["project_id"] == project_id if project_id else True
        return response
    
    yield route_admin_get_project_datapoints_get

@pytest.fixture(scope="function", autouse=True)
def admin_remove_associated_user_from_project_delete(session, client, mock_requests_post):

    def route_admin_remove_associated_user_from_project_delete(authorization_token, 
                             project_id=None,
                             user_id=None,
                             email=None,
                             status_code=200
                             ):
        mock_requests_post()
        url = f"/admin/remove_associated_user_from_project"

        json = {}
        if project_id is not None:
            json["project_id"] = project_id
        if user_id is not None:
            json["user_id"] = user_id
        if email is not None:
            json["email"] = email

        response = client.delete(url, json=json, headers={"Authorization": f'bearer {authorization_token}'})

        assert response.status_code == status_code

        if status_code == 200:
            # Use join to query both tables
            query = session.query(ProjectAssociatedUser).join(
                AssociatedUser, 
                ProjectAssociatedUser.associated_user_id == AssociatedUser.id
            ).filter(
                ProjectAssociatedUser.project_id == project_id
            )
            
            if email:
                query = query.filter(AssociatedUser.email == email)
            elif user_id:
                query = query.filter(AssociatedUser.user_id == user_id)
                
            project_user = query.first()
            
            assert project_user.active == False


        return response

    yield route_admin_remove_associated_user_from_project_delete


@pytest.fixture(scope="session", autouse=True)
def download_urls_get(session, client):
    def route_download_urls_post(authorization_token, 
                             project_id=None,
                             status_code=200
                             ):

        url = "/download-urls/" + (str(project_id) if project_id is not None else "")

        overall_status_before_request = calculate_overall_project_state(session, project_id)["status"]

        response = client.get(url, headers={"Authorization": f'bearer {authorization_token}'})

        assert response.status_code == status_code
        
        if status_code == 200:

            assert calculate_overall_project_state(session, project_id)["status"] == "DATA_DOWNLOADED"
        else:

            assert overall_status_before_request == calculate_overall_project_state(session, project_id)["status"]
        
        return response

    yield route_download_urls_post


@pytest.fixture(scope="session", autouse=True)
def admin_update_project_put(session, client):
    def route_admin_update_project_put(authorization_token, 
                             project_id=None,
                             approved_url=None,
                             status_code=200
                             ):
        
        json = {}
        if approved_url is not None:
            json["approved_url"] = approved_url
        if project_id is not None:
            json["project_id"] = project_id

        url = "admin/projects"

        response = client.put(url, json=json, headers={"Authorization": f'bearer {authorization_token}'})

        assert response.status_code == status_code
        
        if status_code == 200:

            project = session.query(Project).filter(Project.id == project_id).first()

            assert project.approved_url == approved_url
        
        elif status_code == 404:

            project = session.query(Project).filter(Project.id == project_id).first()

            assert project is None
        
        return response
    
    yield route_admin_update_project_put


@pytest.fixture(scope="session", autouse=True)
def admin_get_approved_url_get(session, client):
    def route_admin_get_approved_url_get(authorization_token, 
                             project_id=None,
                             status_code=200
                             ):

        url = "/admin/project/approved-url/" + (str(project_id) if project_id is not None else "")

        response = client.get(url, headers={"Authorization": f'bearer {authorization_token}'})

        assert response.status_code == status_code
        
        if status_code == 200:

            project = session.query(Project).filter(Project.id == project_id).first()

            assert project.approved_url == response.json["approved_url"]

        if status_code == 404:

            project = session.query(Project).filter(Project.id == project_id).first()

            assert project is None or project.approved_url is None
        
        return response

    yield route_admin_get_approved_url_get


@pytest.fixture(scope="session", autouse=True)
def admin_get_project_status_history_get(session, client):
    def route_admin_get_project_status_history_get(authorization_token, 
                             project_id=None,
                             status_code=200
                             ):

        url = "/admin/project/status-history/" + (str(project_id) if project_id is not None else "")

        response = client.get(url, headers={"Authorization": f'bearer {authorization_token}'})

        assert response.status_code == status_code
        
        if status_code == 200:

            sql = """
            SELECT
                state.code,
                state.id,
                request_has_state.create_date,
                request.id,
                consortium_data_contributor.code
            FROM request_has_state
            JOIN request ON request_has_state.request_id = request.id
            JOIN state ON state.id = request_has_state.state_id
            JOIN consortium_data_contributor ON consortium_data_contributor.id = request.consortium_data_contributor_id
            WHERE request.project_id = :project_id
            ORDER BY request.id, request_has_state.create_date DESC;
            """

            """
            Example query: 
               code    | id |        create_date         |  id  |   code   
            -----------+----+----------------------------+------+----------
            IN_REVIEW |  1 | 2026-01-08 17:45:08.6449   | 1605 | INRG
            APPROVED  |  3 | 2026-01-08 17:45:08.742821 | 1606 | INSTRUCT
            IN_REVIEW |  1 | 2026-01-08 17:45:08.6449   | 1606 | INSTRUCT
            """

            """
            response.json = {"INRG": [{"state": "IN_REVIEW", "create_date": "2023-01-01T00:00:00"}],
                             "INSTRUCT": [
                                    {"state": "IN_REVIEW", "create_date": "2023-01-02T00:00:00"}, 
                                    {"state": "APPROVED", "create_date": "2023-01-01T00:00:00"}
                            ]
                            }
            """

            result = session.execute(text(sql), {"project_id": project_id}).fetchall()

            print(response.json)

            for status_update in result:

                #iterate through result and make sure each consortium code is a key in response.json
                #then check that the state and create_date match and make sure the order of the states is correct
                # based on create_date descending
                consortium_code = status_update[-1]
                state_code = status_update[0]
                create_date = status_update[2].isoformat()
                assert consortium_code in response.json
                found = False
                for i, resp_status in enumerate(response.json[consortium_code]):
                    print(resp_status)
                    if resp_status["state"] == state_code and resp_status["create_date"] == create_date:
                        found = True
                        # Check that create_date is later than the previous state if it exists
                        if i > 0:
                            prev_create_date = response.json[consortium_code][i-1]["create_date"]
                            assert resp_status["create_date"] >= prev_create_date, f"Create date {resp_status['create_date']} should be later than or equal to previous state date {prev_create_date}"
                        break
                assert found, f"Status update for consortium {consortium_code} with state {state_code} and create_date {create_date} not found in response."

        return response

    yield route_admin_get_project_status_history_get

@pytest.fixture(scope="session", autouse=True)
def admin_states_get(session, client):
    def route_admin_states_get(authorization_token, 
                             status_code=200
                             ):

        url = "/admin/states"

        response = client.get(url, headers={"Authorization": f'bearer {authorization_token}'})

        assert response.status_code == status_code
        
        if status_code == 200:

            states = session.query(State).all()

            assert len(response.json) == len(states) - 1  # Exclude DEPRECATED state

            for resp_state, state in zip(response.json, [s for s in states if s.code != "DEPRECATED"]):
                assert resp_state["id"] == state.id
                assert resp_state["code"] == state.code
        
        return response

    yield route_admin_states_get

@pytest.fixture(scope="session", autouse=True)
def admin_update_project_state_post(session, client):
    def route_admin_update_project_state_post(authorization_token, 
                             project_id=None,
                             state_id=None,
                             consortium_codes=None,
                             status_code=200
                             ):
        
        json = {}
        if state_id is not None:
            json["state_id"] = state_id
        if project_id is not None:
            json["project_id"] = project_id
        if consortium_codes is not None:
            json["consortiums"] = consortium_codes

        # Get the latest request state per consortium for the project
        
        # First, get the latest update_date for each consortium
        sql = """
        SELECT DISTINCT ON (request.id)
            state.code,
            state.id,
            request_has_state.create_date,
            request.id,
            consortium_data_contributor.code
        FROM request_has_state
        JOIN request ON request_has_state.request_id = request.id
        JOIN state ON state.id = request_has_state.state_id
        JOIN consortium_data_contributor ON consortium_data_contributor.id = request.consortium_data_contributor_id
        WHERE request.project_id = :project_id
        ORDER BY request.id, request_has_state.create_date DESC;
        """
        result = session.execute(text(sql), {"project_id": project_id}).fetchall()

        url = "/admin/projects/state"

        response = client.post(url, json=json, headers={"Authorization": f'bearer {authorization_token}'})

        assert response.status_code == status_code

        new_result = session.execute(text(sql), {"project_id": project_id}).fetchall()
        
        if status_code == 200:

            for new_state in new_result:
                if consortium_codes:
                    if new_state[-1] in consortium_codes:
                            assert new_state[1] == state_id
                    else:
                        #look through results list for request.id matching new_state request.id and check state ids match
                        for old_state in result:
                            if new_state[-2] == old_state[-2]:
                                assert new_state[1] == old_state[1]
                                break

                else:
                    #every state id should match state_id
                    assert new_state[1] == state_id
        
        else:
            #all state ids should match previous state ids
            for new_state in new_result:
                for old_state in result:
                    if new_state[-2] == old_state[-2]:
                        assert new_state[1] == old_state[1]
                        break
        
        return response
    
    yield route_admin_update_project_state_post
# Add a finalizer to ensure proper teardown
@pytest.fixture(scope="session", autouse=True)
def teardown(request, app_instance, session):
    def cleanup():
        session.remove()
        # Explicitly pop the app context to avoid the IndexError
        #app_instance.app_context().pop()

    request.addfinalizer(cleanup)

