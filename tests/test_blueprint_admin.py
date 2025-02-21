import pytest
from cdislogging import get_logger
import requests
import copy
import flask
import ast
from amanuensis.config import config
logger = get_logger(__name__)

@pytest.fixture(scope="module", autouse=True)
def admin_user(register_user):
    admin_id, admin_email =  register_user(email=f"admin@test_copy_search_to_user.com", name="admin", role="admin")
    yield admin_id, admin_email



def test_copy_search_to_user_success_from_explorer(register_user, login, filter_set_post, admin_copy_search_to_user_post, admin_user):
    user_id, user_email =  register_user(email=f"user_1@test_copy_search_to_user_success_from_explorer.com", name=__name__)
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id, 
        name="test_copy_search_to_user_success_from_explorer", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]

    user_id_2, user_email_2 =  register_user(email=f"user_2@test_copy_search_to_user_success_from_explorer.com", name=__name__)

    login(admin_user[0], admin_user[1])
    assert admin_copy_search_to_user_post(
        authorization_token=admin_user[0], 
        filter_set_id=filter_set_id,
        user_id=user_id_2
    )

def test_copy_search_to_user_success_from_manual(register_user, login, admin_filter_set_post, admin_copy_search_to_user_post, admin_user):
    user_id, user_email =  register_user(email=f"user_1@test_copy_search_to_user_success_from_manual.com", name=__name__)
    login(admin_user[0], admin_user[1])
    filter_set_id = admin_filter_set_post(
        admin_user[0], 
        user_id=user_id,
        name="test_copy_search_to_user_success_from_manual", 
        description="test_copy_search_to_user_success_from_manual",
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]

    user_id_2, user_email_2 =  register_user(email=f"user_2@test_copy_search_to_user_success_from_manual.com", name=__name__)
    assert admin_copy_search_to_user_post(
        authorization_token=admin_user[0], 
        filter_set_id=filter_set_id,
        user_id=user_id_2
    )


def test_copy_search_to_user_success_from_token(register_user, login, filter_set_post, filter_set_snapshot_post, filter_set_snapshot_get, admin_copy_search_to_user_post, admin_user):
    user_id, user_email =  register_user(email=f"user_1@test_copy_search_to_user_success_from_token.com", name=__name__)
    login(user_id, user_email)
    
    filter_set_id = filter_set_post(
        user_id, 
        name="test_copy_search_to_user_success_from_token", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]

    shareable_token = filter_set_snapshot_post(
        user_id, 
        filter_set_id=filter_set_id
    ).json

    filter_set_from_token = filter_set_snapshot_get(
        user_id, 
        token=shareable_token
    ).json["id"]

    print(filter_set_from_token)

    user_id_2, user_email_2 =  register_user(email=f"user_2@test_copy_search_to_user_success_from_token.com", name=__name__)
    login(admin_user[0], admin_user[1])
    assert admin_copy_search_to_user_post(
        authorization_token=admin_user[0], 
        filter_set_id=filter_set_from_token,
        user_id=user_id_2
    )



def test_copy_search_to_user_success_from_project_search():
    #skip for now as there is no way to access the id of the search connected to the project without accesss to DB
    pass

def test_copy_search_to_user_failed_auth(register_user, login, filter_set_post, admin_copy_search_to_user_post, admin_user):
    user_id, user_email =  register_user(email=f"user_1@test_copy_search_to_user_failed_auth.com", name=__name__)
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id, 
        name="test_copy_search_to_user_failed_auth", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]

    user_id_2, user_email_2 =  register_user(email=f"user_2@test_copy_search_to_user_failed_auth.com", name=__name__)

    assert admin_copy_search_to_user_post(
        authorization_token=user_id, 
        filter_set_id=filter_set_id,
        user_id=user_id_2,
        status_code=403
    )

def test_copy_search_to_user_missing_parameters(register_user, login, filter_set_post, admin_copy_search_to_user_post, admin_user):
    user_id, user_email =  register_user(email=f"user_1@test_copy_search_to_user_missing_parameters.com", name=__name__)
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id, 
        name="test_copy_search_to_user_missing_parameters", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]

    user_id_2, user_email_2 =  register_user(email=f"user_2@test_copy_search_to_user_missing_parameters.com", name=__name__)

    login(admin_user[0], admin_user[1])
    assert admin_copy_search_to_user_post(
        authorization_token=admin_user[0], 
        #filter_set_id=filter_set_id,
        user_id=user_id_2,
        status_code=400
    )

    assert admin_copy_search_to_user_post(
        authorization_token=admin_user[0], 
        filter_set_id=filter_set_id,
        #user_id=user_id_2,
        status_code=400
    )


def test_copy_search_to_user_search_doesnt_exist(register_user, login, filter_set_post, admin_copy_search_to_user_post, admin_user):
    user_id, user_email =  register_user(email=f"user_1@test_copy_search_to_user_search_doesnt_exist.com", name=__name__)
    user_id_2, user_email_2 =  register_user(email=f"user_2@test_copy_search_to_user_search_doesnt_exist.com", name=__name__)

    login(admin_user[0], admin_user[1])
    assert admin_copy_search_to_user_post(
        authorization_token=admin_user[0], 
        filter_set_id=999999,
        user_id=user_id_2,
        status_code=404
    )


def test_upload_file_to_project_success(register_user, login, admin_upload_file, project_post, filter_set_post, admin_user, admin_update_associated_user_role, s3):

    user_id, user_email =  register_user(email=f"user_1@test_upload_file_to_project_success.com", name="test_upload_file_to_project_success")
    login(user_id, user_email)

    filter_set_id = filter_set_post(
        user_id, 
        name="test_upload_file_to_project_success", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]

    project_id = project_post(
        authorization_token=user_id, 
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="This is the description for test_upload_file_to_project_success",
        institution="test_upload_file_to_project_success",
        associated_users_emails=["user_2@test_upload_file_to_project_success.com"],
        name="This is the name for test_upload_file_to_project_success", 
        filter_set_ids=[filter_set_id]
    ).json["id"]

    admin_update_associated_user_role(
        authorization_token=admin_user[0], 
        user_id=user_id,
        project_id=project_id,
        role="DATA_ACCESS"
    )

    login(admin_user[0], admin_user[1])
    url = admin_upload_file(
        authorization_token=admin_user[0], 
        project_id=project_id,
        key="file.txt",
    ).json

    with open("tests/data/file.txt", "rb") as f:
        # Perform the PUT request to upload the file
        upload_file_response = requests.put(url, data=f)
    
    uploaded_file_response = s3.get_object(Bucket="amanuensis-upload-file-test-bucket", Key="file.txt")

    assert upload_file_response.status_code == 200
    assert uploaded_file_response['ResponseMetadata']['HTTPStatusCode'] == 200


def test_upload_file_to_project_and_then_send_email_success(register_user, login, admin_upload_file, project_post, filter_set_post, admin_user, pytestconfig, admin_update_associated_user_role, s3):
    
    if not pytestconfig.getoption("--test-emails-to-send-notifications"):
        logger.warnings("Skipping test_upload_file_to_test_upload_file_to_project_and_then_send_email_successproject_success as no email to send notifications is provided will be marked as fail")
        assert False
    
    else:
        email_list = ast.literal_eval(pytestconfig.getoption("--test-emails-to-send-notifications")) if pytestconfig.getoption("--test-emails-to-send-notifications") else []

    user_id, user_email =  register_user(email=email_list[0], name=email_list[0])
    other_user_ids = []
    for email in email_list[1:]:
        other_user_id, other_user_email = register_user(email=email, name=email)
        other_user_ids.append(other_user_id)
    login(user_id, user_email)

    filter_set_id = filter_set_post(
        user_id, 
        name="test_upload_file_to_project_and_then_send_email_success", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]

    project_id = project_post(
        authorization_token=user_id, 
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="This is the description for test_upload_file_to_project_and_then_send_email_success",
        institution="test_upload_file_to_project_and_then_send_email_success",
        associated_users_emails=email_list[1:] if len(email_list) > 1 else [],
        name="This is the name for test_upload_file_to_project_and_then_send_email_success", 
        filter_set_ids=[filter_set_id]
    ).json["id"]

    admin_update_associated_user_role(
        authorization_token=admin_user[0], 
        user_id=user_id,
        project_id=project_id,
        role="DATA_ACCESS"
    )
    for other_user_id in other_user_ids:
        admin_update_associated_user_role(
            authorization_token=admin_user[0], 
            user_id=other_user_id,
            project_id=project_id,
            role="DATA_ACCESS"
        )

    login(admin_user[0], admin_user[1])
    url = admin_upload_file(
        authorization_token=admin_user[0], 
        project_id=project_id,
        key="file.txt",
    ).json

    assert url

def test_upload_file_to_project_failed_missing_parameters(register_user, login, admin_upload_file, project_post, filter_set_post, admin_user, admin_update_associated_user_role, s3):
    user_id, user_email =  register_user(email=f"user_1@test_upload_file_to_project_failed_missing_parameters.com", name="test_uptest_upload_file_to_project_failed_missing_parameters")
    login(user_id, user_email)

    filter_set_id = filter_set_post(
        user_id, 
        name="test_upload_file_to_project_failed_missing_parameters", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]

    project_id = project_post(
        authorization_token=user_id, 
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="This is the description for test_upload_file_to_project_failed_missing_parameters",
        institution="test_upload_file_to_project_failed_missing_parameters",
        associated_users_emails=["user_2@test_upload_file_to_project_failed_missing_parameters.com"],
        name="This is the name for test_upload_file_to_project_failed_missing_parameters", 
        filter_set_ids=[filter_set_id]
    ).json["id"]

    admin_update_associated_user_role(
        authorization_token=admin_user[0], 
        user_id=user_id,
        project_id=project_id,
        role="DATA_ACCESS"
    )

    login(admin_user[0], admin_user[1])
    assert admin_upload_file(
        authorization_token=admin_user[0], 
        project_id=project_id,
        status_code=400
    )

    assert admin_upload_file(
        authorization_token=admin_user[0], 
        key="file.txt",
        status_code=400
    )


def test_upload_file_to_project_failed_project_doesnt_exist(register_user, login, admin_upload_file, project_post, filter_set_post, admin_user, admin_update_associated_user_role, s3):
    user_id, user_email =  register_user(email=f"user_1@test_upload_file_to_project_failed_project_doesnt_exist.com", name="test_upload_file_to_project_failed_project_doesnt_exist")
    login(user_id, user_email)

    filter_set_id = filter_set_post(
        user_id, 
        name="test_upload_file_to_project_failed_project_doesnt_exist", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]

    login(admin_user[0], admin_user[1])
    assert admin_upload_file(
        authorization_token=admin_user[0], 
        project_id=999999,
        key="file.txt",
        status_code=404
    )

def test_upload_file_to_project_failed_auth(register_user, login, admin_upload_file, project_post, filter_set_post, admin_user, admin_update_associated_user_role, s3):
    user_id, user_email =  register_user(email=f"user_1@test_upload_file_to_project_failed_auth.com", name="test_uptest_upload_file_to_project_failed_auth")
    login(user_id, user_email)

    filter_set_id = filter_set_post(
        user_id, 
        name="test_upload_file_to_project_failed_auth", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]

    project_id = project_post(
        authorization_token=user_id, 
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="This is the description for test_upload_file_to_project_failed_auth",
        institution="test_upload_file_to_project_failed_auth",
        associated_users_emails=["user_2@test_upload_file_to_project_failed_auth.com"],
        name="This is the name for test_upload_file_to_project_failed_auth", 
        filter_set_ids=[filter_set_id]
    ).json["id"]

    admin_update_associated_user_role(
        authorization_token=admin_user[0], 
        user_id=user_id,
        project_id=project_id,
        role="DATA_ACCESS"
    )

    assert admin_upload_file(
        authorization_token=user_id, 
        project_id=project_id,
        status_code=403
    )

def test_upload_file_to_project_failed_s3_error(register_user, login, admin_upload_file, project_post, filter_set_post, admin_user, admin_update_associated_user_role, s3):
    user_id, user_email =  register_user(email=f"user_1@test_upload_file_to_project_failed_s3_error.com", name="test_uptest_upload_file_to_project_failed_s3_error")
    login(user_id, user_email)

    filter_set_id = filter_set_post(
        user_id, 
        name="test_upload_file_to_project_failed_s3_error", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]

    project_id = project_post(
        authorization_token=user_id, 
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="This is the description for test_upload_file_to_project_failed_s3_error",
        institution="test_upload_file_to_project_failed_s3_error",
        associated_users_emails=["user_2@test_upload_file_to_project_failed_s3_error.com"],
        name="This is the name for test_upload_file_to_project_failed_s3_error", 
        filter_set_ids=[filter_set_id]
    ).json["id"]

    admin_update_associated_user_role(
        authorization_token=admin_user[0], 
        user_id=user_id,
        project_id=project_id,
        role="DATA_ACCESS"
    )

    login(admin_user[0], admin_user[1])

    copy_of_boto = copy.copy(flask.current_app.s3_boto)
    flask.current_app.s3_boto = None
    assert admin_upload_file(
        authorization_token=admin_user[0], 
        project_id=project_id,
        key="file.txt",
        status_code=500
    )

    flask.current_app.s3_boto = copy_of_boto
    bucket_name = config["AWS_CREDENTIALS"]["DATA_DELIVERY_S3_BUCKET"]["bucket_name"]
    del config["AWS_CREDENTIALS"]["DATA_DELIVERY_S3_BUCKET"]["bucket_name"]

    assert admin_upload_file(
        authorization_token=admin_user[0], 
        project_id=project_id,
        key="file.txt",
        status_code=500
    )

    
    config["AWS_CREDENTIALS"]["DATA_DELIVERY_S3_BUCKET"]["bucket_name"] = bucket_name


