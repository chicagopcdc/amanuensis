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
