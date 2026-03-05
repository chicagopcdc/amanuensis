import pytest

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
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG", "INTERACT"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG", "INTERACT"]}}]}
    ).json["id"]

    login(admin_user[0], admin_user[1])
    assert admin_copy_search_to_project(
        authorization_token=admin_user[0], 
        filter_set_id=filter_set_id_2,
        project_id=project_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG", "INTERACT"]
    )

def test_copy_search_to_project_add_request_none_removed_move_state_back_to_IN_REVIEW(register_user, login, filter_set_post, project_post, admin_update_project_state_post, admin_states_get, admin_copy_search_to_project, admin_user):
    user_id, user_email =  register_user(email=f"user_1@test_copy_search_to_project_add_request_none_removed_move_state_back_to_IN_REVIEW.com", name=__name__)
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id, 
        name="test_copy_search_to_project_add_request_none_removed_move_state_back_to_IN_REVIEW", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]

    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_copy_search_to_project_add_request_none_removed_move_state_back_to_IN_REVIEW",
        institution="test_copy_search_to_project_add_request_none_removed_move_state_back_to_IN_REVIEW",
        associated_users_emails=[],
        name="test_copy_search_to_project_add_request_none_removed_move_state_back_to_IN_REVIEW", 
        filter_set_ids=[filter_set_id]
    ).json["id"]

    states = admin_states_get(
        authorization_token=user_id,
        status_code=200
    )
    for state in states.json:
        if state["code"] == "APPROVED":
            state_id = state["id"]
    assert admin_update_project_state_post(
        authorization_token=admin_user[0],
        project_id=project_id,
        state_id=state_id,
        status_code=200
    )

    filter_set_id_2 = filter_set_post(
        user_id, 
        name="test_copy_search_to_project_add_request_none_removed_move_state_back_to_IN_REVIEW_2", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG", "INTERACT"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG", "INTERACT"]}}]}
    ).json["id"]

    login(admin_user[0], admin_user[1])
    assert admin_copy_search_to_project(
        authorization_token=admin_user[0], 
        filter_set_id=filter_set_id_2,
        project_id=project_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG", "INTERACT"]
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

def test_copy_search_to_project_none_added_but_request_removed_move_state_back_to_IN_REVIEW(register_user, login, filter_set_post, project_post, admin_update_project_state_post, admin_states_get, admin_copy_search_to_project, admin_user):
    user_id, user_email =  register_user(email=f"user_1@test_copy_search_to_project_none_added_but_request_removed_move_state_back_to_IN_REVIEW.com", name=__name__)
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id, 
        name="test_copy_search_to_project_none_added_but_request_removed_move_state_back_to_IN_REVIEW", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_copy_search_to_project_none_added_but_request_removed_move_state_back_to_IN_REVIEW",
        institution="test_copy_search_to_project_none_added_but_request_removed_move_state_back_to_IN_REVIEW",
        associated_users_emails=[],
        name="test_copy_search_to_project_none_added_but_request_removed_move_state_back_to_IN_REVIEW", 
        filter_set_ids=[filter_set_id]
    ).json["id"]
    states = admin_states_get(
        authorization_token=user_id,
        status_code=200
    )
    for state in states.json:
        if state["code"] == "APPROVED":
            state_id = state["id"]
    assert admin_update_project_state_post(
        authorization_token=admin_user[0],
        project_id=project_id,
        state_id=state_id,
        status_code=200
    )
    filter_set_id_2 = filter_set_post(
        user_id, 
        name="test_copy_search_to_project_none_added_but_request_removed_move_state_back_to_IN_REVIEW_2", 
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


def test_change_filter_set_project_in_data_downloaded(register_user, login, filter_set_post, project_post, admin_update_project_state_post, admin_states_get, admin_copy_search_to_project, admin_user):
    user_id, user_email =  register_user(email=f"user_1@test_change_filter_set_project_in_data_downloaded.com", name=__name__)
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_change_filter_set_project_in_data_downloaded",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_change_filter_set_project_in_data_downloaded",
        institution="test_change_filter_set_project_in_data_downloaded",
        associated_users_emails=[],
        name="test_change_filter_set_project_in_data_downloaded",
        filter_set_ids=[filter_set_id]
    ).json["id"]

    login(admin_user[0], admin_user[1])
    states = admin_states_get(
        authorization_token=admin_user[0],
        status_code=200
    )
    for state in states.json:
        if state["code"] == "DATA_DOWNLOADED":
            state_id = state["id"]
    assert admin_update_project_state_post(
        authorization_token=admin_user[0],
        project_id=project_id,
        state_id=state_id,
        status_code=200
    )
    login(user_id, user_email)
    filter_set_id_2 = filter_set_post(
        user_id, 
        name="test_copy_search_to_project_none_added_but_request_removed_2", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]

    login(admin_user[0], admin_user[1])
    assert admin_copy_search_to_project(
        authorization_token=admin_user[0], 
        filter_set_id=filter_set_id_2,
        project_id=project_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        state_code="APPROVED",
    )

def test_change_filter_set_project_in_data_available(register_user, login, filter_set_post, project_post, admin_update_project_state_post, admin_states_get, admin_copy_search_to_project, admin_update_project_put, admin_user, patch_ses_client, admin_update_associated_user_role):
    patch_ses_client()
    user_id, user_email =  register_user(email=f"user_1@test_change_filter_set_project_in_data_available.com", name=__name__)
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_change_filter_set_project_in_data_available",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_change_filter_set_project_in_data_available",
        institution="test_change_filter_set_project_in_data_available",
        associated_users_emails=[],
        name="test_change_filter_set_project_in_data_available",
        filter_set_ids=[filter_set_id]
    ).json["id"]

    admin_update_project_put(
        authorization_token=admin_user[0],
        project_id=project_id,
        approved_url="http://approved.url/test_change_filter_set_project_in_data_available",
        status_code=200
    )
    assert admin_update_associated_user_role(
        authorization_token=admin_user[0],
        user_id=user_id,
        project_id=project_id,
        role="DATA_ACCESS",
        status_code=200
    )  

    login(admin_user[0], admin_user[1])
    states = admin_states_get(
        authorization_token=admin_user[0],
        status_code=200
    )
    for state in states.json:
        if state["code"] == "DATA_AVAILABLE":
            state_id = state["id"]
    assert admin_update_project_state_post(
        authorization_token=admin_user[0],
        project_id=project_id,
        state_id=state_id,
        status_code=200
    )
    login(user_id, user_email)
    filter_set_id_2 = filter_set_post(
        user_id, 
        name="test_copy_search_to_project_none_added_but_request_removed_2", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]

    login(admin_user[0], admin_user[1])
    assert admin_copy_search_to_project(
        authorization_token=admin_user[0], 
        filter_set_id=filter_set_id_2,
        project_id=project_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        state_code="APPROVED",
    )