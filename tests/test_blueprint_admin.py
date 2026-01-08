import pytest
from cdislogging import get_logger
import requests
import copy
import flask
import ast
from amanuensis.config import config
logger = get_logger(__name__)
from amanuensis.models import *
from time import sleep
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
        logger.warning("Skipping test_upload_file_to_test_upload_file_to_project_and_then_send_email_successproject_success as no email to send notifications is provided will be marked as fail")
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




def test_copy_search_to_project_no_request_change(register_user, login, filter_set_post, project_post,  admin_copy_search_to_project, admin_user):
    user_id, user_email =  register_user(email=f"user_1@test_copy_search_to_project_no_request_change.com", name=__name__)
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id, 
        name="test_copy_search_to_project_no_request_change", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]

    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_copy_search_to_project_no_request_change",
        institution="test_copy_search_to_project_no_request_change",
        associated_users_emails=[],
        name="test_copy_search_to_project_no_request_change", 
        filter_set_ids=[filter_set_id]
    ).json["id"]

    filter_set_id_2 = filter_set_post(
        user_id, 
        name="test_copy_search_to_project_no_request_change_2", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]

    login(admin_user[0], admin_user[1])
    assert admin_copy_search_to_project(
        authorization_token=admin_user[0], 
        filter_set_id=filter_set_id_2,
        project_id=project_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"]
    )

def test_copy_search_to_project_add_request_none_removed(register_user, login, filter_set_post, project_post,  admin_copy_search_to_project, admin_user):
    user_id, user_email =  register_user(email=f"user_1@test_copy_search_to_project_add_request_none_removed.com", name=__name__)
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id, 
        name="test_copy_search_to_project_add_request_none_removed", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]

    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_copy_search_to_project_add_request_none_removed",
        institution="test_copy_search_to_project_add_request_none_removed",
        associated_users_emails=[],
        name="test_copy_search_to_project_add_request_none_removed", 
        filter_set_ids=[filter_set_id]
    ).json["id"]

    filter_set_id_2 = filter_set_post(
        user_id, 
        name="test_copy_search_to_project_add_request_none_removed_2", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG", "INSTRUCT"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG", "INSTRUCT"]}}]}
    ).json["id"]

    login(admin_user[0], admin_user[1])
    assert admin_copy_search_to_project(
        authorization_token=admin_user[0], 
        filter_set_id=filter_set_id_2,
        project_id=project_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG", "INSTRUCT"]
    )

def test_copy_search_to_project_none_added_but_request_removed(register_user, login, filter_set_post, project_post,  admin_copy_search_to_project, admin_user):
    user_id, user_email =  register_user(email=f"user_1@test_copy_search_to_project_none_added_but_request_removed.com", name=__name__)
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id, 
        name="test_copy_search_to_project_none_added_but_request_removed", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]

    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_copy_search_to_project_none_added_but_request_removed",
        institution="test_copy_search_to_project_none_added_but_request_removed",
        associated_users_emails=[],
        name="test_copy_search_to_project_none_added_but_request_removed", 
        filter_set_ids=[filter_set_id]
    ).json["id"]

    filter_set_id_2 = filter_set_post(
        user_id, 
        name="test_copy_search_to_project_none_added_but_request_removed_2", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT"]}}]}
    ).json["id"]

    login(admin_user[0], admin_user[1])
    assert admin_copy_search_to_project(
        authorization_token=admin_user[0], 
        filter_set_id=filter_set_id_2,
        project_id=project_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT"]
    )

def test_copy_search_to_project_add_request_remove_request(register_user, login, filter_set_post, project_post,  admin_copy_search_to_project, admin_user):
    user_id, user_email =  register_user(email=f"user_1@test_copy_search_to_project_add_request_remove_request.com", name=__name__)
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id, 
        name="test_copy_search_to_project_add_request_remove_request", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]

    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_copy_search_to_project_add_request_remove_request",
        institution="test_copy_search_to_project_add_request_remove_request",
        associated_users_emails=[],
        name="test_copy_search_to_project_add_request_remove_request", 
        filter_set_ids=[filter_set_id]
    ).json["id"]

    filter_set_id_2 = filter_set_post(
        user_id, 
        name="test_copy_search_to_project_add_request_remove_request_2", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INTERACT"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INTERACT"]}}]}
    ).json["id"]

    login(admin_user[0], admin_user[1])
    assert admin_copy_search_to_project(
        authorization_token=admin_user[0], 
        filter_set_id=filter_set_id_2,
        project_id=project_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INTERACT"]
    )

def test_copy_search_to_project_fail_missing_parameters(register_user, login, filter_set_post, project_post,  admin_copy_search_to_project, admin_user):
    user_id, user_email =  register_user(email=f"user_1@test_copy_search_to_project_fail_missing_parameters.com", name=__name__)
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id, 
        name="test_copy_search_to_project_fail_missing_parameters", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]

    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_copy_search_to_project_fail_missing_parameters",
        institution="test_copy_search_to_project_fail_missing_parameters",
        associated_users_emails=[],
        name="test_copy_search_to_project_fail_missing_parameters", 
        filter_set_ids=[filter_set_id]
    ).json["id"]

    login(admin_user[0], admin_user[1])
    assert admin_copy_search_to_project(
        authorization_token=admin_user[0], 
        #filter_set_id=filter_set_id_2,
        project_id=project_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INTERACT"],
        status_code=400
    )

    assert admin_copy_search_to_project(
        authorization_token=admin_user[0], 
        filter_set_id=filter_set_id,
        #project_id=project_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INTERACT"],
        status_code=400
    )

def test_copy_search_to_project_fail_searchs_do_not_exist(register_user, login, filter_set_post, project_post,  admin_copy_search_to_project, admin_user):
    user_id, user_email =  register_user(email=f"user_1@test_copy_search_to_project_fail_searchs_do_not_exist.com", name=__name__)
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id, 
        name="test_copy_search_to_project_fail_searchs_do_not_exist", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]

    project_id = project_post(
        authorization_token=user_id,
        description="test_copy_search_to_project_fail_searchs_do_not_exist",
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        institution="test_copy_search_to_project_fail_searchs_do_not_exist",
        associated_users_emails=[],
        name="test_copy_search_to_project_fail_searchs_do_not_exist", 
        filter_set_ids=[filter_set_id]
    ).json["id"]

    login(admin_user[0], admin_user[1])
    assert admin_copy_search_to_project(
        authorization_token=admin_user[0], 
        filter_set_id=[999999],
        project_id=project_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INTERACT"],
        status_code=404
    )

    assert admin_copy_search_to_project(
        authorization_token=admin_user[0], 
        filter_set_id=[filter_set_id, 999999],
        project_id=project_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INTERACT"],
        status_code=400
    )


def test_copy_search_to_project_fail_project_doesnt_exist(register_user, login, filter_set_post, project_post,  admin_copy_search_to_project, admin_user):
    user_id, user_email =  register_user(email=f"user_1@test_copy_search_to_project_fail_project_doesnt_exist.com", name=__name__)
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id, 
        name="test_copy_search_to_project_fail_project_doesnt_exist", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]

    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_copy_search_to_project_fail_project_doesnt_exist",
        institution="test_copy_search_to_project_fail_project_doesnt_exist",
        associated_users_emails=[],
        name="test_copy_search_to_project_fail_project_doesnt_exist", 
        filter_set_ids=[filter_set_id]
    ).json["id"]

    login(admin_user[0], admin_user[1])
    assert admin_copy_search_to_project(
        authorization_token=admin_user[0], 
        filter_set_id=[filter_set_id],
        project_id=999999,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INTERACT"],
        status_code=404
    )

def test_copy_search_to_project_fail_user_not_admin( register_user, login, filter_set_post, project_post,  admin_copy_search_to_project, admin_user):
    user_id, user_email =  register_user(email=f"user_1@test_copy_search_to_project_fail_user_not_admin.com", name=__name__)
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id, 
        name="test_copy_search_to_project_fail_user_not_admin", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]

    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_copy_search_to_project_fail_user_not_admin",
        institution="test_copy_search_to_project_fail_user_not_admin",
        associated_users_emails=[],
        name="test_copy_search_to_project_fail_user_not_admin", 
        filter_set_ids=[filter_set_id]
    ).json["id"]

    assert admin_copy_search_to_project(
        authorization_token=user_id, 
        filter_set_id=[filter_set_id],
        project_id=project_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INTERACT"],
        status_code=403
    )

def test_change_filter_set_project_in_data_downloaded_or_data_available(register_user, login, filter_set_post, project_post,  admin_copy_search_to_project, admin_user):
    pass
    #this needs the change state endpoint to make this work



def test_get_filter_sets_by_project_success(register_user, login, filter_set_post, project_post, admin_filter_set_by_project_id_get, admin_user):
    user_id, user_email =  register_user(email=f"user_1@test_get_filter_sets_by_project_success.com", name=__name__)
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_get_filter_sets_by_project_success",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_get_filter_sets_by_project_success",
        institution="test_get_filter_sets_by_project_success",
        associated_users_emails=[],
        name="test_get_filter_sets_by_project_success",
        filter_set_ids=[filter_set_id]
    ).json["id"]

    assert admin_filter_set_by_project_id_get(
        authorization_token=admin_user[0],
        project_id=project_id,
        status_code=200
    )


def test_get_filter_sets_by_project_success_no_filter_sets(register_user, login, filter_set_post, project_post, admin_filter_set_by_project_id_get, admin_user):
    pass
    #this isnt possible at the moment

def test_get_filter_sets_by_project_success_after_project_filter_sets_change(register_user, login, filter_set_post, project_post, admin_copy_search_to_project, admin_filter_set_by_project_id_get, admin_user):
    user_id, user_email =  register_user(email=f"user_1@test_get_filter_sets_by_project_success_after_project_filter_sets_change.com", name=__name__)
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_get_filter_sets_by_project_success_after_project_filter_sets_change",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_get_filter_sets_by_project_success_after_project_filter_sets_change",
        institution="test_get_filter_sets_by_project_success_after_project_filter_sets_change",
        associated_users_emails=[],
        name="test_get_filter_sets_by_project_success_after_project_filter_sets_change",
        filter_set_ids=[filter_set_id]
    ).json["id"]

    filter_set_id_2 = filter_set_post(
        user_id,
        name="test_get_filter_sets_by_project_success_after_project_filter_sets_change_2",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INTERACT"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INTERACT"]}}]}
    ).json["id"]

    login(admin_user[0], admin_user[1])
    assert admin_copy_search_to_project(
        authorization_token=admin_user[0],
        filter_set_id=filter_set_id_2,
        project_id=project_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INTERACT"]
    )

    filter_sets = admin_filter_set_by_project_id_get(
        authorization_token=admin_user[0],
        project_id=project_id,
        status_code=200
    ).json

    assert filter_sets[0]["name"] == "test_get_filter_sets_by_project_success_after_project_filter_sets_change_test_get_filter_sets_by_project_success_after_project_filter_sets_change_2" 

def test_get_filter_sets_by_project_fail_user_not_admin(register_user, login, filter_set_post, project_post, admin_filter_set_by_project_id_get, admin_user):
    user_id, user_email =  register_user(email=f"user_1@test_get_filter_sets_by_project_fail_user_not_admin.com", name=__name__)
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_get_filter_sets_by_project_fail_user_not_admin",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_get_filter_sets_by_project_fail_user_not_admin",
        institution="test_get_filter_sets_by_project_fail_user_not_admin",
        associated_users_emails=[],
        name="test_get_filter_sets_by_project_fail_user_not_admin",
        filter_set_ids=[filter_set_id]
    ).json["id"]

    assert admin_filter_set_by_project_id_get(
        authorization_token=user_id,
        project_id=project_id,
        status_code=403
    )

def test_get_filter_sets_by_project_fail_missing_parameters(register_user, login, filter_set_post, project_post, admin_filter_set_by_project_id_get, admin_user):
    user_id, user_email =  register_user(email=f"user_1@test_get_filter_sets_by_project_fail_missing_parameters.com", name=__name__)
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_get_filter_sets_by_project_fail_missing_parameters",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_get_filter_sets_by_project_fail_missing_parameters",
        institution="test_get_filter_sets_by_project_fail_missing_parameters",
        associated_users_emails=[],
        name="test_get_filter_sets_by_project_fail_missing_parameters",
        filter_set_ids=[filter_set_id]
    ).json["id"]

    assert admin_filter_set_by_project_id_get(
        authorization_token=admin_user[0],
        #project_id=project_id,
        status_code=404
    )

def test_get_filter_sets_by_project_fail_project_doesnt_exist(register_user, login, filter_set_post, project_post, admin_filter_set_by_project_id_get, admin_user):
    user_id, user_email =  register_user(email=f"user_1@test_get_filter_sets_by_project_fail_project_doesnt_exist.com", name=__name__)
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_get_filter_sets_by_project_fail_project_doesnt_exist",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_get_filter_sets_by_project_fail_project_doesnt_exist",
        institution="test_get_filter_sets_by_project_fail_project_doesnt_exist",
        associated_users_emails=[],
        name="test_get_filter_sets_by_project_fail_project_doesnt_exist",
        filter_set_ids=[filter_set_id]
    ).json["id"]

    assert admin_filter_set_by_project_id_get(
        authorization_token=admin_user[0],
        project_id=999999,
        status_code=404
    )

def test_add_user_to_project(register_user, login, filter_set_post, project_post, admin_user, admin_associated_user_post):

    user_id, user_email = register_user(email=f"user1@test_add_user_to_project.com", name="user1")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id, 
        name="test_add_user_to_project", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]

    project_id = project_post(
        authorization_token=user_id, 
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_add_user_to_project",
        institution="test_add_user_to_project",
        associated_users_emails=[],
        name="test_add_user_to_project", 
        filter_set_ids=[filter_set_id]
    ).json["id"]

    admin_id, admin_email = admin_user
    login(admin_id, admin_email)
    #with email in fence
    user_2_id, user_2_email = register_user(email=f"user_2@test_add_user_to_project.com", name="user_2")
    assert admin_associated_user_post(
        authorization_token=admin_id,
        users=[{"email":user_2_email, "project_id":project_id}]
    )

    #with email not in fence
    assert admin_associated_user_post(
        authorization_token=admin_id,
        users=[{"email":"user_3@test_add_user_to_project.com", "project_id":project_id}]
    )

    #with id in fence
    user_4_id, user_4_email = register_user(email=f"user_4@test_add_user_to_project.com", name="user_4")
    assert admin_associated_user_post(
        authorization_token=admin_id,
        users=[{"id":user_4_id, "project_id":project_id}]
    )

    #with id and email in fence
    user_5_id, user_5_email = register_user(email=f"user_5@test_add_user_to_project.com", name="user_5")
    assert admin_associated_user_post(
        authorization_token=admin_id,
        users=[{"id":user_5_id, "email":user_5_email, "project_id":project_id}]
    )

    #with role
    user_6_id, user_6_email = register_user(email=f"user_6@test_add_user_to_project.com", name="user_6")
    assert admin_associated_user_post(
        authorization_token=admin_id,
        role="DATA_ACCESS",
        users=[{"id":user_6_id, "email":user_6_email, "project_id":project_id}]
    )

    #readd user
    assert admin_associated_user_post(
        authorization_token=admin_id,
        users=[{"id":user_6_id, "email":user_6_email, "project_id":project_id}]
    )


def test_add_user_to_project_fail_missing_inputs(register_user, login, filter_set_post, project_post, admin_user, admin_associated_user_post):
    user_id, user_email = register_user(email=f"user1@test_add_user_to_project_fail_missing_inputs.com", name="user1")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id, 
        name="test_add_user_to_project_fail_missing_inputs", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id, 
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_add_user_to_project_fail_missing_inputs",
        institution="test_add_user_to_project_fail_missing_inputs",
        associated_users_emails=[],
        name="test_add_user_to_project_fail_missing_inputs", 
        filter_set_ids=[filter_set_id]
    ).json["id"]

    admin_id, admin_email = admin_user
    login(admin_id, admin_email)
    assert admin_associated_user_post(
        authorization_token=admin_id,
        users=[{"email":"user_2@test_add_user_to_project_fail_missing_inputs.com"}],
        status_code=400
    )

    assert admin_associated_user_post(
        authorization_token=admin_id,
        users=[{"id":user_id}],
        status_code=400
    )

    assert admin_associated_user_post(
        authorization_token=admin_id,
        users=[{"project_id":project_id}],
        status_code=400
    )

    assert admin_associated_user_post(
        authorization_token=admin_id,
        users=[{}],
        status_code=400
    )

def test_add_user_to_project_fail_project_not_found(register_user, login, filter_set_post, project_post, admin_user, admin_associated_user_post):
    user_id, user_email = register_user(email=f"user1@test_add_user_to_project_fail_project_not_found.com", name="user1")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id, 
        name="test_add_user_to_project_fail_project_not_found", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id, 
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_add_user_to_project_fail_project_not_found",
        institution="test_add_user_to_project_fail_project_not_found",
        associated_users_emails=[],
        name="test_add_user_to_project_fail_project_not_found", 
        filter_set_ids=[filter_set_id]
    ).json["id"]

    admin_id, admin_email = admin_user
    login(admin_id, admin_email)
    assert admin_associated_user_post(
        authorization_token=admin_id,
        users=[{"email":"user_2@test_add_user_to_project_fail_project_not_found.com", "project_id":999999}],
        status_code=404
    )

def test_add_user_to_project_fail_user_information_doesnt_match(register_user, login, filter_set_post, project_post, admin_user, admin_associated_user_post):
    user_id, user_email = register_user(email=f"user1@test_add_user_to_project_fail_user_information_doesnt_match.com", name="user1")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id, 
        name="test_add_user_to_project_fail_user_information_doesnt_match", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id, 
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_add_user_to_project_fail_user_information_doesnt_match",
        institution="test_add_user_to_project_fail_user_information_doesnt_match",
        associated_users_emails=[],
        name="test_add_user_to_project_fail_user_information_doesnt_match", 
        filter_set_ids=[filter_set_id]
    ).json["id"]

    admin_id, admin_email = admin_user
    login(admin_id, admin_email)

    
    


    #email does not exist in fence and id is present
    assert admin_associated_user_post(
        authorization_token=admin_id,
        users=[{"email":"user_2@test_add_user_to_project_fail_user_information_doesnt_match.com", "id":user_id, "project_id":project_id}],
        status_code=400
    )

    #email exists in fence but id doesnt match email
    user_id_2, user_email_2 = register_user(email=f"user_2@test_add_user_to_project_fail_user_information_doesnt_match.com", name="user_2")
    assert admin_associated_user_post(
        authorization_token=admin_id,
        users=[{"email":user_email_2, "id":user_id, "project_id":project_id}],
        status_code=400
    )


def test_add_user_to_project_fail_user_id_doesnt_exist(register_user, login, filter_set_post, project_post, admin_user, admin_associated_user_post):
    user_id, user_email = register_user(email=f"user1@test_add_user_to_project_fail_user_id_doesnt_exist.com", name="user1")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id, 
        name="test_add_user_to_project_fail_user_id_doesnt_exist", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id, 
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_add_user_to_project_fail_user_id_doesnt_exist",
        institution="test_add_user_to_project_fail_user_id_doesnt_exist",
        associated_users_emails=[],
        name="test_add_user_to_project_fail_user_id_doesnt_exist", 
        filter_set_ids=[filter_set_id]
    ).json["id"]

    admin_id, admin_email = admin_user
    login(admin_id, admin_email)
    assert admin_associated_user_post(
        authorization_token=admin_id,
        users=[{"id":999999, "project_id":project_id}],
        status_code=400
    )

def test_add_user_to_project_fail_missing_auth(register_user, login, filter_set_post, project_post, admin_user, admin_associated_user_post):
    user_id, user_email = register_user(email=f"user1@test_add_user_to_project_fail_missing_auth.com", name="user1")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id, 
        name="test_add_user_to_project_fail_missing_auth", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id, 
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_add_user_to_project_fail_missing_auth",
        institution="test_add_user_to_project_fail_missing_auth",
        associated_users_emails=[],
        name="test_add_user_to_project_fail_missing_auth", 
        filter_set_ids=[filter_set_id]
    ).json["id"]
    assert admin_associated_user_post(
        authorization_token=user_id,
        users=[{"email":"user_2@test_add_user_to_project_fail_missing_auth.com", "project_id":project_id}],
        status_code=403
    )

def test_remove_associated_user_from_project_success(register_user, login, filter_set_post, project_post, admin_user, admin_remove_associated_user_from_project_delete):
    user_id, user_email = register_user(email=f"user1@test_remove_associated_user_from_project_success.com", name="user1")
    user_3_id, user_3_email = register_user(email=f"user_3@test_remove_associated_user_from_project_success.com", name="user_3")
    user_6_id, user_6_email = register_user(email=f"user_6@test_remove_associated_user_from_project_success.com", name="user_6")
    user_7_id, user_7_email = register_user(email=f"user_7@test_remove_associated_user_from_project_success.com", name="user_7")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id, 
        name="test_remove_associated_user_from_project_success", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id, 
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_remove_associated_user_from_project_success",
        institution="test_remove_associated_user_from_project_success",
        associated_users_emails=["user_2@test_remove_associated_user_from_project_success.com", 
                                 "user_3@test_remove_associated_user_from_project_success.com", 
                                 "user_4@test_remove_associated_user_from_project_success.com", 
                                 "user_5@test_remove_associated_user_from_project_success.com", 
                                 "user_6@test_remove_associated_user_from_project_success.com",
                                 "user_7@test_remove_associated_user_from_project_success.com"],
        name="test_remove_associated_user_from_project_success", 
        filter_set_ids=[filter_set_id]
    ).json["id"]


    #what happens when user is added to project before signing up
    #then user signs up but never goes to the data request page so their user_id doesnt get updated in table
    #then user is removed from project using their user_id
    admin_id, admin_email = admin_user
    login(admin_id, admin_email)
    user_2_id, user_2_email = register_user(email=f"user_2@test_remove_associated_user_from_project_success.com", name="user_2")
    assert admin_remove_associated_user_from_project_delete(
        authorization_token=admin_id,
        project_id=project_id,
        user_id=user_2_id
    )

    #same thing as above but both user_id and email
    user_5_id, user_5_email = register_user(email=f"user_5@test_remove_associated_user_from_project_success.com", name="user_5")
    assert admin_remove_associated_user_from_project_delete(
        authorization_token=admin_id,
        project_id=project_id,
        user_id=user_5_id,
        email=user_5_email
    )

    #user who is in fence before being added to project
    assert admin_remove_associated_user_from_project_delete(
        authorization_token=admin_id,
        project_id=project_id,
        user_id=user_3_id
    )

    #user who is in fence after being added to project delete with email
    assert admin_remove_associated_user_from_project_delete(
        authorization_token=admin_id,
        project_id=project_id,
        email="user_6@test_remove_associated_user_from_project_success.com"
    )

    #user who is in fence delete with both user_id and email
    assert admin_remove_associated_user_from_project_delete(
        authorization_token=admin_id,
        project_id=project_id,
        user_id=user_7_id,
        email="user_7@test_remove_associated_user_from_project_success.com"
    )

    #user who is not in fence
    assert admin_remove_associated_user_from_project_delete(
        authorization_token=admin_id,
        project_id=project_id,
        email="user_4@test_remove_associated_user_from_project_success.com"
    )

def test_remove_associated_user_from_project_fail_missing_auth(register_user, login, filter_set_post, project_post, admin_user, admin_remove_associated_user_from_project_delete):
    user_id, user_email = register_user(email=f"user1@test_remove_associated_user_from_project_fail_missing_auth.com", name="user1")
    user_2_id, user_2_email = register_user(email=f"user_2@test_remove_associated_user_from_project_fail_missing_auth.com", name="user_2")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_remove_associated_user_from_project_fail_missing_auth",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_remove_associated_user_from_project_fail_missing_auth",
        institution="test_remove_associated_user_from_project_fail_missing_auth",
        associated_users_emails=[user_2_email],
        name="test_remove_associated_user_from_project_fail_missing_auth",
        filter_set_ids=[filter_set_id]
    ).json["id"]

    assert admin_remove_associated_user_from_project_delete(
        authorization_token=user_id,
        project_id=project_id,
        user_id=user_2_id,
        status_code=403
    )

def test_remove_associated_user_from_project_fail_missing_inputs(register_user, login, filter_set_post, project_post, admin_user, admin_remove_associated_user_from_project_delete):
    user_id, user_email = register_user(email=f"user1@test_remove_associated_user_from_project_fail_missing_inputs.com", name="user1")
    user_2_id, user_2_email = register_user(email=f"user_2@test_remove_associated_user_from_project_fail_missing_inputs.com", name="user_2")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_remove_associated_user_from_project_fail_missing_inputs",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_remove_associated_user_from_project_fail_missing_inputs",
        institution="test_remove_associated_user_from_project_fail_missing_inputs",
        associated_users_emails=[user_2_email],
        name="test_remove_associated_user_from_project_fail_missing_inputs",
        filter_set_ids=[filter_set_id]
    ).json["id"]
    
    admin_id, admin_email = admin_user
    login(admin_id, admin_email)
    assert admin_remove_associated_user_from_project_delete(
        authorization_token=admin_id,
        project_id=project_id,
        status_code=400
    )

    assert admin_remove_associated_user_from_project_delete(
        authorization_token=admin_id,
        user_id=user_2_id,
        status_code=400
    )

    assert admin_remove_associated_user_from_project_delete(
        authorization_token=admin_id,
        email=user_2_email,
        status_code=400
    )


def test_remove_associated_user_from_project_fail_user_not_found(register_user, login, filter_set_post, project_post, admin_user, admin_remove_associated_user_from_project_delete):
    user_id, user_email = register_user(email=f"user1@test_remove_associated_user_from_project_fail_user_not_found.com", name="user1")
    user_2_id, user_2_email = register_user(email=f"user_2@test_remove_associated_user_from_project_fail_user_not_found.com", name="user_2")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_remove_associated_user_from_project_fail_user_not_found",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_remove_associated_user_from_project_fail_user_not_found",
        institution="test_remove_associated_user_from_project_fail_user_not_found",
        associated_users_emails=[user_2_email],
        name="test_remove_associated_user_from_project_fail_user_not_found",
        filter_set_ids=[filter_set_id]
    ).json["id"]

    admin_id, admin_email = admin_user
    login(admin_id, admin_email)
    assert admin_remove_associated_user_from_project_delete(
        authorization_token=admin_id,
        project_id=project_id,
        user_id=999999,
        status_code=404
    )

    assert admin_remove_associated_user_from_project_delete(
        authorization_token=admin_id,
        project_id=project_id,
        email="user_3@test_remove_associated_user_from_project_fail_user_not_found.com",
        status_code=404
    )

def test_remove_associated_user_from_project_fail_user_not_associated_with_project(register_user, login, filter_set_post, project_post, admin_user, admin_remove_associated_user_from_project_delete):
    user_id, user_email = register_user(email=f"user1@test_remove_associated_user_from_project_fail_user_not_associated_with_project.com", name="user1")
    user_2_id, user_2_email = register_user(email=f"user_2@test_remove_associated_user_from_project_fail_user_not_associated_with_project.com", name="user_2")
    user_3_id, user_3_email = register_user(email=f"user_3@test_remove_associated_user_from_project_fail_user_not_associated_with_project.com", name="user_3")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_remove_associated_user_from_project_fail_user_not_associated_with_project",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_remove_associated_user_from_project_fail_user_not_associated_with_project",
        institution="test_remove_associated_user_from_project_fail_user_not_associated_with_project",
        associated_users_emails=[user_2_email],
        name="test_remove_associated_user_from_project_fail_user_not_associated_with_project",
        filter_set_ids=[filter_set_id]
    ).json["id"]

    admin_id, admin_email = admin_user
    login(admin_id, admin_email)
    #person has already been removed
    assert admin_remove_associated_user_from_project_delete(
        authorization_token=admin_id,
        project_id=project_id,
        email=user_2_email,
        status_code=200
    )
    assert admin_remove_associated_user_from_project_delete(
        authorization_token=admin_id,
        project_id=project_id,
        user_id=user_2_id,
        status_code=404
    )
    #person was never associated with project
    assert admin_remove_associated_user_from_project_delete(
        authorization_token=admin_id,
        project_id=project_id,
        user_id=user_3_id,
        status_code=404
    )

def test_remove_associated_user_from_project_fail_project_not_found(register_user, login, filter_set_post, project_post, admin_user, admin_remove_associated_user_from_project_delete):
    user_id, user_email = register_user(email=f"user1@test_remove_associated_user_from_project_fail_project_not_found.com", name="user1")
    user_2_id, user_2_email = register_user(email=f"user_2@test_remove_associated_user_from_project_fail_project_not_found.com", name="user_2")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_remove_associated_user_from_project_fail_project_not_found",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_remove_associated_user_from_project_fail_project_not_found",
        institution="test_remove_associated_user_from_project_fail_project_not_found",
        associated_users_emails=[user_2_email],
        name="test_remove_associated_user_from_project_fail_project_not_found",
        filter_set_ids=[filter_set_id]
    ).json["id"]

    admin_id, admin_email = admin_user
    login(admin_id, admin_email)
    assert admin_remove_associated_user_from_project_delete(
        authorization_token=admin_id,
        project_id=999999,
        user_id=user_2_id,
        status_code=404
    )

def test_remove_associated_user_from_project_fail_attempt_to_remove_owner(register_user, login, filter_set_post, project_post, admin_user, admin_remove_associated_user_from_project_delete):
    user_id, user_email = register_user(email=f"user1@test_remove_associated_user_from_project_fail_attempt_to_remove_owner.com", name="user1")
    user_2_id, user_2_email = register_user(email=f"user_2@test_remove_associated_user_from_project_fail_attempt_to_remove_owner.com", name="user_2")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_remove_associated_user_from_project_fail_attempt_to_remove_owner",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_remove_associated_user_from_project_fail_attempt_to_remove_owner",
        institution="test_remove_associated_user_from_project_fail_attempt_to_remove_owner",
        associated_users_emails=[user_2_email],
        name="test_remove_associated_user_from_project_fail_attempt_to_remove_owner",
        filter_set_ids=[filter_set_id]
    ).json["id"]

    admin_id, admin_email = admin_user
    login(admin_id, admin_email)
    assert admin_remove_associated_user_from_project_delete(
        authorization_token=admin_id,
        project_id=project_id,
        user_id=user_id,
        status_code=400
    )

    #attempt with email
    assert admin_remove_associated_user_from_project_delete(
        authorization_token=admin_id,
        project_id=project_id,
        email=user_email,
        status_code=400
    )

    #attempt with both
    assert admin_remove_associated_user_from_project_delete(
        authorization_token=admin_id,
        project_id=project_id,
        user_id=user_id,
        email=user_email,
        status_code=400
    )


def test_download_url_with_new_aws_version(register_user, session, login, filter_set_post, project_post, admin_user, download_urls_get, admin_update_associated_user_role):
    #dont run with normal test suit at moment
    # if True:
    #     pass
    # else:
    user_id, user_email = register_user(email=f"user1@test_download_url_with_new_aws_version.com", name="user1")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_download_url_with_new_aws_version",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_download_url_with_new_aws_version",
        institution="test_download_url_with_new_aws_version",
        associated_users_emails=[],
        name="test_download_url_with_new_aws_version",
        filter_set_ids=[filter_set_id]
    ).json["id"]

    admin_update_associated_user_role(
        authorization_token=admin_user[0], 
        user_id=user_id,
        project_id=project_id,
        role="DATA_ACCESS"
    )

    session.query(Project).filter(Project.id == project_id).update({"approved_url": "https://gen3-helm-pelican-export.s3.amazonaws.com/test.json"})
    session.commit()

    login(user_id, user_email)
    assert download_urls_get(
        authorization_token=user_id,
        project_id=project_id,
        status_code=200
    )

    session.query(Project).filter(Project.id == project_id).update({"approved_url": "https://gen3-helm-pelican-export.s3.us-east-1.amazonaws.com/test.json"})
    session.commit()

    login(user_id, user_email)
    assert download_urls_get(
        authorization_token=user_id,
        project_id=project_id,
        status_code=200
    )


def test_admin_update_project_put_success(register_user, login, filter_set_post, project_post, admin_user, admin_update_project_put):
    user_id, user_email = register_user(email=f"user1@test_change_project_approved_url_success.com", name="user1")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_change_project_approved_url_success",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_change_project_approved_url_success",
        institution="test_change_project_approved_url_success",
        associated_users_emails=[],
        name="test_change_project_approved_url_success",
        filter_set_ids=[filter_set_id]
    ).json["id"]

    assert admin_update_project_put(
        authorization_token=admin_user[0],
        project_id=project_id,
        approved_url="https://amanuensis-bucket.s3.amazonaws.com/test.json",
        status_code=200
    )

def test_admin_update_project_put_fail_user_not_admin(register_user, login, filter_set_post, project_post, admin_user, admin_update_project_put):
    user_id, user_email = register_user(email=f"user1@test_admin_update_project_put_fail_user_not_admin.com", name="user1")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_admin_update_project_put_fail_user_not_admin",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_admin_update_project_put_fail_user_not_admin",
        institution="test_admin_update_project_put_fail_user_not_admin",
        associated_users_emails=[],
        name="test_admin_update_project_put_fail_user_not_admin",
        filter_set_ids=[filter_set_id]
    ).json["id"]

    assert admin_update_project_put(
        authorization_token=user_id,
        project_id=project_id,
        approved_url="https://amanuensis-bucket.s3.amazonaws.com/test.json",
        status_code=403
    )

def test_admin_update_project_put_fail_missing_parameters(register_user, login, filter_set_post, project_post, admin_user, admin_update_project_put):
    user_id, user_email = register_user(email=f"user1@test_admin_update_project_put_fail_missing_parameters.com", name="user1")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_admin_update_project_put_fail_missing_parameters",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_admin_update_project_put_fail_missing_parameters",
        institution="test_admin_update_project_put_fail_missing_parameters",
        associated_users_emails=[],
        name="test_admin_update_project_put_fail_missing_parameters",
        filter_set_ids=[filter_set_id]
    ).json["id"]

    assert admin_update_project_put(
        authorization_token=admin_user[0],
        approved_url="https://amanuensis-bucket.s3.amazonaws.com/test.json",
        status_code=400
    )

    assert admin_update_project_put(
        authorization_token=admin_user[0],
        project_id=project_id,
        status_code=400
    )

    assert admin_update_project_put(
        authorization_token=admin_user[0],
        project_id=999999,
        approved_url="https://amanuensis-bucket.s3.amazonaws.com/test.json",
        status_code=404
    )

def test_get_approved_url_success(register_user, login, filter_set_post, project_post, admin_user, admin_update_project_put, admin_get_approved_url_get):
    user_id, user_email = register_user(email=f"user1@test_get_approved_url_success.com", name="user1")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_get_approved_url_success",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_get_approved_url_success",
        institution="test_get_approved_url_success",
        associated_users_emails=[],
        name="test_get_approved_url_success",
        filter_set_ids=[filter_set_id]
    ).json["id"]

    assert admin_update_project_put(
        authorization_token=admin_user[0],
        project_id=project_id,
        approved_url="https://amanuensis-bucket.s3.amazonaws.com/test.json",
        status_code=200
    )

    assert admin_get_approved_url_get(
        authorization_token=admin_user[0],
        project_id=project_id,
        status_code=200
    )

def test_get_approved_url_fail_user_not_admin(register_user, login, filter_set_post, project_post, admin_user, admin_get_approved_url_get):
    user_id, user_email = register_user(email=f"user1@test_get_approved_url_fail_user_not_admin.com", name="user1")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_get_approved_url_fail_user_not_admin",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_get_approved_url_fail_user_not_admin",
        institution="test_get_approved_url_fail_user_not_admin",
        associated_users_emails=[],
        name="test_get_approved_url_fail_user_not_admin",
        filter_set_ids=[filter_set_id]
    ).json["id"]

    assert admin_get_approved_url_get(
        authorization_token=user_id,
        project_id=project_id,
        status_code=403
    )

def test_get_approved_url_fail_missing_parameters(register_user, login, filter_set_post, project_post, admin_user, admin_update_project_put, admin_get_approved_url_get):
    user_id, user_email = register_user(email=f"user1@test_get_approved_url_fail_missing_parameters.com", name="user1")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_get_approved_url_fail_missing_parameters",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_get_approved_url_fail_missing_parameters",
        institution="test_get_approved_url_fail_missing_parameters",
        associated_users_emails=[],
        name="test_get_approved_url_fail_missing_parameters",
        filter_set_ids=[filter_set_id]
    ).json["id"]

    assert admin_get_approved_url_get(
        authorization_token=admin_user[0],
        status_code=404
    )

    assert admin_update_project_put(
        authorization_token=admin_user[0],
        project_id=project_id,
        approved_url="https://amanuensis-bucket.s3.amazonaws.com/test.json",
        status_code=200
    )

    assert admin_get_approved_url_get(
        authorization_token=admin_user[0],
        status_code=404
    )

    assert admin_get_approved_url_get(
        authorization_token=admin_user[0],
        project_id=999999,
        status_code=404
    )

def test_admin_update_associated_user_role(register_user, login, filter_set_post, project_post, admin_user, admin_update_associated_user_role):
    user_id, user_email = register_user(email=f"user1@test_admin_update_associated_user_role.com", name="user1")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_admin_update_associated_user_role",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_admin_update_associated_user_role",
        institution="test_admin_update_associated_user_role",
        associated_users_emails=["user2@test_admin_update_associated_user_role.com"],
        name="test_admin_update_associated_user_role",
        filter_set_ids=[filter_set_id]
    ).json["id"] 
    assert admin_update_associated_user_role(
        authorization_token=admin_user[0],
        user_id=user_id,
        project_id=project_id,
        role="DATA_ACCESS",
        status_code=200
    )  
    #User is not signed up yet role cannot be changed
    assert admin_update_associated_user_role(
        authorization_token=admin_user[0],
        email="user2@test_admin_update_associated_user_role.com",
        project_id=project_id,
        role="DATA_ACCESS",
        status_code=400
    ) 