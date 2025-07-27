import pytest 
from unittest.mock import MagicMock, patch
from flask import Flask
import flask

from amanuensis.resources.userdatamodel.associated_users import create_associated_user
from amanuensis.resources.userdatamodel.project import create_project

@pytest.fixture(scope="module", autouse=True)
def s3(app_instance):
    mock_s3_client = MagicMock()
    # Mock methods you use
    mock_s3_client.create_bucket.return_value = None
    mock_s3_client.list_buckets.return_value = {'Buckets': []}
    mock_s3_client.delete_object.return_value = None
    mock_s3_client.list_objects_v2.return_value = {'Contents': []}

    with patch.object(app_instance.s3_boto, 's3_client', mock_s3_client):
        yield mock_s3_client

@pytest.fixture(scope="module", autouse=True)
def users(session, register_user):
    user_id, user_email = register_user(email=f"user_1@{__name__}.com", name=__name__)
    admin_id, admin_email = register_user(email=f"admin@{__name__}.com", name=__name__, role="admin")

    user = create_associated_user(session, email=user_email, user_id=user_id)
    admin = create_associated_user(session,email=admin_email, user_id=admin_id)

    yield user, admin

@pytest.fixture(scope="function")
def gen_project(session, register_user, login, project_post, filter_set_post, users):
    def _make_project(name="gen_project"):
        login(users[0].user_id, users[0].email)

        with flask.current_app.db.session as session:
            project = create_project(
                session,
                name=name,
                description=name,
                institution=name,
                user_id=users[0].user_id
            )
        return project.id

    return _make_project

def test_get_datapoints(gen_project,
                           users,
                           admin_add_project_datapoints_post,
                           admin_get_project_datapoints_get):    
    project_data = gen_project(name="test_get_datapoints")
    project_data_1 = gen_project(name="test_get_datapoints_1")
    project_data_2 = gen_project(name="test_get_datapoints_2")
    
    assert admin_add_project_datapoints_post(
        authorization_token=users[1].email,
        term = "test_get_datapoints",
        value_list = ["test_get_datapoints"],
        type = "w",
        project_id = project_data
    )
    assert admin_add_project_datapoints_post(
        authorization_token=users[1].email,
        term = "test_get_datapoints_1",
        value_list = ["test_get_datapoints","other_value"],
        type = "b",
        project_id = project_data_1
    )
    assert admin_add_project_datapoints_post(
        authorization_token=users[1].email,
        term = "test_get_datapoints_2",
        value_list = ["test_get_datapoints","other_value", "other_value_2"],
        type = "w",
        project_id = project_data_2
    )

    response = admin_get_project_datapoints_get(
        authorization_token=users[1].email,
        type = "w",
        many = True
    ).get_json()
    assert len(response) == 2
    assert response[0]["term"] == "test_get_datapoints"
    assert response[1]["term"] == "test_get_datapoints_2"

    response = admin_get_project_datapoints_get(
        authorization_token=users[1].email,
        type = "w",
    ).get_json()
    assert response["term"] == "test_get_datapoints"

    response = admin_get_project_datapoints_get(
        authorization_token=users[1].email,
        type = "b",
    ).get_json()
    assert response["term"] == "test_get_datapoints_1"

    response = admin_get_project_datapoints_get(
        authorization_token=users[1].email,
        type = "z",
        status_code = 404
    ).get_json()

def test_create_datapoints_success(gen_project,
                           users,
                           admin_add_project_datapoints_post,
                           admin_get_project_datapoints_get):    
    project_data = gen_project(name="test_create_datapoints_success")
    
    assert admin_add_project_datapoints_post(
        authorization_token=users[1].email,
        term = "test_create_datapoints_success",
        value_list = ["test_create_datapoints_success"],
        type = "w",
        project_id = project_data
    )

    assert admin_add_project_datapoints_post(
        authorization_token=users[1].email,
        term = "test_create_datapoints_success_2",
        value_list = ["test_create_datapoints_success_2"],
        type = "b",
        project_id = project_data
    )

    response = admin_get_project_datapoints_get(
        authorization_token=users[1].email,
        project_id = project_data,
        many = True
    ).get_json()
    assert response[0]["active"] == True
    assert response[0]["term"] == "test_create_datapoints_success"
    assert response[0]["value_list"] == ["test_create_datapoints_success"]
    assert response[0]["type"] == "w"
    assert response[0]["project_id"] == project_data

    assert response[1]["active"] == True
    assert response[1]["term"] == "test_create_datapoints_success_2"
    assert response[1]["value_list"] == ["test_create_datapoints_success_2"]
    assert response[1]["type"] == "b"
    assert response[1]["project_id"] == project_data

def test_identicle_datapoints_failiure(gen_project,
                           users,
                           admin_add_project_datapoints_post,
                           admin_get_project_datapoints_get):  
    project_data = gen_project(name="test_identicle_datapoints_failiure")    
    
    assert admin_add_project_datapoints_post(
        authorization_token=users[1].email,
        term = "test_identicle_datapoints_failiure",
        value_list = ["test_identicle_datapoints_failiure"],
        type = "w",
        project_id = project_data
    )

    assert admin_add_project_datapoints_post(
        authorization_token=users[1].email,
        term = "test_identicle_datapoints_failiure",
        value_list = ["test_1_value_list_val_1"],
        type = "w",
        project_id = project_data,
        status_code = 400
    )
    response = admin_get_project_datapoints_get(
        authorization_token=users[1].email,
        project_id = project_data
    )
    
def test_create_datapoints_failure(gen_project,
                           users,
                           admin_add_project_datapoints_post,
                           admin_get_project_datapoints_get
                           ):    
    # user_id, user_email =  register_user(email=f"user@test_create_datapoints.com", name="test_create_datapoints")
    # login(user_id, user_email)
    project_data = gen_project(name="test_create_datapoints_failure")

    assert admin_add_project_datapoints_post(
        authorization_token=users[1].email,
        term = "test_1_create_datapoints_term",
        value_list = ["test_1_value_list_val_1"],
        type = "Z",
        project_id = project_data,
        status_code = 400
    ) 

    assert admin_add_project_datapoints_post( 
        authorization_token=users[1].email,
        term = "test_1_create_datapoints_term",
        value_list = ["test_1_value_list_val_1"],
        type = "w",
        project_id = 9999999,
        status_code = 400
    ) 

    assert admin_add_project_datapoints_post(
        authorization_token=users[1].email,
        term = "test_1_create_datapoints_term",
        value_list = "not a list",
        type = "w",
        project_id = project_data,
        status_code = 400
    )
    assert admin_add_project_datapoints_post(
        authorization_token=users[1].email,
        term = None,
        value_list = ["test_1_value_list_val_1"],
        type = "w",
        project_id = project_data,
        status_code = 400
    )
    assert admin_get_project_datapoints_get(
        authorization_token=users[1].email,
        project_id = project_data,
        status_code = 404
    )

def test_delete_datapoints_success(gen_project,
                           users,
                           admin_add_project_datapoints_post,
                           admin_get_project_datapoints_get,
                           admin_delete_project_datapoints_delete):  
    project_data = gen_project(name="test_delete_datapoints_success")
    assert admin_add_project_datapoints_post(
        authorization_token=users[1].email,
        term = "test_delete_datapoints_success",
        value_list = ["test_delete_datapoints_success"],
        type = "w",
        project_id = project_data
    )
    response = admin_get_project_datapoints_get(
        authorization_token=users[1].email,
        project_id = project_data
    ).get_json()
    assert response["term"] == "test_delete_datapoints_success"
    assert response["active"] == True

    deletion_response = admin_delete_project_datapoints_delete(
        authorization_token=users[1].email,
        id = response["id"]
    ).get_json()
    assert deletion_response["active"] == False

    response = admin_get_project_datapoints_get(
        authorization_token=users[1].email,
        id = response["id"],
        status_code = 404
    )
    assert response 

def test_delete_datapoints_failure(
                           users,
                           admin_delete_project_datapoints_delete):  
    assert admin_delete_project_datapoints_delete(
        authorization_token=users[1].email,
        id = 999999999,
        status_code = 404
    )

def test_reactivate_datapoints(gen_project,
                           users,
                           admin_add_project_datapoints_post,
                           admin_get_project_datapoints_get,
                           admin_delete_project_datapoints_delete,
                           admin_reactivate_project_datapoints_post):  
    project_data = gen_project(name="test_reactivate_datapoints")
    response = admin_add_project_datapoints_post(
        authorization_token=users[1].email,
        term = "test_reactivate_datapoints",
        value_list = ["test_reactivate_datapoints"],
        type = "w",
        project_id = project_data
    ).get_json()

    deletion_response = admin_delete_project_datapoints_delete(
        authorization_token=users[1].email,
        id = response["id"]
    ).get_json()
    assert deletion_response["active"] == False

    assert admin_get_project_datapoints_get(
        authorization_token=users[1].email,
        id = response["id"],
        status_code = 404
    )
    assert admin_reactivate_project_datapoints_post(
        authorization_token=users[1].email,
        id = response["id"]
    )

    response = admin_get_project_datapoints_get(
        authorization_token=users[1].email,
        id = response["id"],
    ).get_json()
    assert response["active"] == True

def test_update_datapoints(gen_project,
                           users,
                           admin_add_project_datapoints_post,
                           admin_get_project_datapoints_get,
                           admin_modify_project_datapoints_post
                           ):    
    project_data = gen_project(name="test_update_datapoints")
    
    assert admin_add_project_datapoints_post(
        authorization_token=users[1].email,
        term = "test_update_datapoints",
        value_list = ["test_update_datapoints"],
        type = "w",
        project_id = project_data
    )
    
    response = admin_get_project_datapoints_get(
        authorization_token=users[1].email,
        project_id = project_data,
    ).get_json()

    assert response["term"] == "test_update_datapoints"
    assert response["value_list"] == ["test_update_datapoints"]
    assert response["type"] == "w"
    assert response["project_id"] == project_data

    assert admin_modify_project_datapoints_post(
        id = response["id"],
        authorization_token=users[1].email,
        term = "test_update_datapoints_different",
        value_list = ["test_update_datapoints", "test_update_datapoints_different"],
        type = "b"
    )

    response = admin_get_project_datapoints_get(
        authorization_token=users[1].email,
        project_id = project_data,
    ).get_json()

    assert response["term"] == "test_update_datapoints_different"
    assert response["value_list"] == ["test_update_datapoints", "test_update_datapoints_different"]
    assert response["type"] == "b"
    assert response["project_id"] == project_data

    other_project_data = gen_project(name="test_update_datapoints_different")

    response = admin_modify_project_datapoints_post(
        id = response["id"],
        authorization_token=users[1].email,
        project_id = other_project_data
    ).get_json()
    assert response["project_id"] == other_project_data

    response = admin_get_project_datapoints_get(
        authorization_token=users[1].email,
        id = response["id"],
    ).get_json()
    assert response["project_id"] == other_project_data
