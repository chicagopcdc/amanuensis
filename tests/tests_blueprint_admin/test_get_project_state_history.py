def test_get_project_state_history(register_user, login, filter_set_post, project_post, admin_user, admin_get_project_status_history_get):
    user_id, user_email = register_user(email=f"user1@test_get_project_state_history.com", name="user1")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_get_project_state_history",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_get_project_state_history",
        institution="test_get_project_state_history",
        associated_users_emails=[],
        name="test_get_project_state_history",
        filter_set_ids=[filter_set_id]
    ).json["id"]

    assert admin_get_project_status_history_get(
        authorization_token=admin_user[0],
        project_id=project_id,
        history_dict={"INRG": ["IN_REVIEW"] , "INSTRUCT": ["IN_REVIEW"]},
        status_code=200
    )

def test_get_project_state_history_after_project_state_change(register_user, login, filter_set_post, project_post, admin_user, admin_update_project_state_post, admin_states_get, admin_get_project_status_history_get):
    user_id, user_email = register_user(email=f"user1@test_get_project_state_history_after_project_state_change.com", name="user1")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_get_project_state_history_after_project_state_change",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_get_project_state_history_after_project_state_change",
        institution="test_get_project_state_history_after_project_state_change",
        associated_users_emails=[],
        name="test_get_project_state_history_after_project_state_change",
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
        input_consortium_codes=["INSTRUCT"],
        status_code=200
    )

    assert admin_get_project_status_history_get(
        authorization_token=admin_user[0],
        project_id=project_id,
        history_dict={"INRG": ["IN_REVIEW"] , "INSTRUCT": ["APPROVED", "IN_REVIEW"]},
        status_code=200
    )