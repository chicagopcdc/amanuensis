def test_post_admin_update_associated_user_role(register_user, login, filter_set_post, project_post, admin_user, admin_update_associated_user_role):
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

