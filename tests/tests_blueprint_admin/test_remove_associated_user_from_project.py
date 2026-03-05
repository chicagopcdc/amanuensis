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
