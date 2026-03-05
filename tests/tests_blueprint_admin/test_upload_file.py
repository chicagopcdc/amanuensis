import requests
from cdislogging import get_logger
import ast
import copy
import flask
from amanuensis.config import config
logger = get_logger(__name__)

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

