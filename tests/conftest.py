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
from sqlalchemy import or_, and_
from amanuensis.errors import AuthError

logger = get_logger(logger_name=__name__)
from amanuensis.models import ConsortiumDataContributor
from flask import request

def pytest_addoption(parser):
    parser.addoption(
        "--configuration-file",  # The CLI argument
        action="store",   # Stores the value passed to this argument
        default="amanuensis-config.yaml",  # The default value
        help="Path to the config file"
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
        session.query(Notification).delete()
        session.query(NotificationLog).delete()

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
            username = fence_user[0]["name"]
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
            associated_users_in_fence = [find_fence_user({"ids":[authorization_token]})["users"][0]["name"]]
            associated_users_not_in_fence = []

            for associated_user in associated_users_emails:
                fence_user = find_fence_user({"usernames":[associated_user]})["users"]

                if not fence_user:
                    associated_users_not_in_fence.append(associated_user)

                elif fence_user[0]["id"] == authorization_token:
                    continue

                else:
                    associated_users_in_fence.append(fence_user[0]["name"])

            assert len(updated_associated_users) == len(associated_users_in_fence + associated_users_not_in_fence)

            for updated_associated_user in updated_associated_users:

                if not updated_associated_user.user_id:

                    assert updated_associated_user.email in associated_users_not_in_fence

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
            assert filter_set.filter_object == filter_object
            assert filter_set.graphql_object == graphql_object
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
            assert filter_set_after_url.name == name if name is not None else filter_set.name
            assert filter_set_after_url.filter_object == filter_object if filter_object is not None else filter_set.filter_object
            assert filter_set_after_url.graphql_object == graphql_object if graphql_object is not None else filter_set.graphql_object
            assert filter_set_after_url.description == description if description is not None else filter_set.description
            print(True if filter_object is not None or graphql_object is not None else filter_set.is_valid)
            print(filter_set_after_url.is_valid)
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
            assert filter_set.filter_object == None
            assert filter_set.graphql_object == graphql_object
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

# Add a finalizer to ensure proper teardown
@pytest.fixture(scope="session", autouse=True)
def teardown(request, app_instance, session):
    def cleanup():
        session.remove()
        # Explicitly pop the app context to avoid the IndexError
        #app_instance.app_context().pop()

    request.addfinalizer(cleanup)

