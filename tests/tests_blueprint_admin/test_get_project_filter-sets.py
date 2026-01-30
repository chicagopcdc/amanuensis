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
