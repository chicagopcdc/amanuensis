import pytest
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