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
