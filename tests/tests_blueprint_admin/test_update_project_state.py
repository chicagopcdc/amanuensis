from amanuensis.models import RequestState, Request, Project, ConsortiumDataContributor, State
def test_post_project_state(register_user, login, filter_set_post, project_post, admin_user, admin_update_project_state_post, admin_states_get):
    user_id, user_email = register_user(email=f"user1@test_post_project_state.com", name="user1")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_post_project_state",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_post_project_state",
        institution="test_post_project_state",
        associated_users_emails=[],
        name="test_post_project_state",
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

def test_post_project_state_success_with_consortium_list(register_user, login, filter_set_post, project_post, admin_user, admin_update_project_state_post, admin_states_get):
    user_id, user_email = register_user(email=f"user1@test_post_project_state_success_with_consortium_list.com", name="user1")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_post_project_state_success_with_consortium_list",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_post_project_state_success_with_consortium_list",
        institution="test_post_project_state_success_with_consortium_list",
        associated_users_emails=[],
        name="test_post_project_state_success_with_consortium_list",
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

def test_post_project_state_success_with_consortium_list_dont_create_duplicate_states(session, register_user, login, filter_set_post, project_post, admin_user, admin_update_project_state_post, admin_states_get):
    user_id, user_email = register_user(email=f"user1@test_post_project_state_success_with_consortium_list_dont_create_duplicate_states.com", name="user1")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_post_project_state_success_with_consortium_list_dont_create_duplicate_states",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_post_project_state_success_with_consortium_list_dont_create_duplicate_states",
        institution="test_post_project_state_success_with_consortium_list_dont_create_duplicate_states",
        associated_users_emails=[],
        name="test_post_project_state_success_with_consortium_list_dont_create_duplicate_states",
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

    # Try to set the same state again for the same consortium, should not create duplicate states
    assert admin_update_project_state_post(
        authorization_token=admin_user[0],
        project_id=project_id,
        state_id=state_id,
        status_code=200
    )

    instruct_request_states = (
        session.query(RequestState)
        .join(RequestState.request)
        .join(Request.consortium_data_contributor)
        .filter(Request.project_id == project_id, ConsortiumDataContributor.code == "INSTRUCT")
        .all()
    )
    assert len(instruct_request_states) == 2  # Only one state should exist for INSTRUCT consortium

def test_post_project_state_unauthorized_user(register_user, login, filter_set_post, project_post, admin_user, admin_update_project_state_post, admin_states_get):
    user_id, user_email = register_user(email=f"user1@test_post_project_state_unauthorized_user.com", name="user1")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_post_project_state_unauthorized_user",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_post_project_state_unauthorized_user",
        institution="test_post_project_state_unauthorized_user",
        associated_users_emails=[],
        name="test_post_project_state_unauthorized_user",
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
        authorization_token=user_id,
        project_id=project_id,
        state_id=state_id,
        status_code=403
    )

def test_post_project_state_invalid_state_id(register_user, login, filter_set_post, project_post, admin_user, admin_update_project_state_post, admin_states_get):
    user_id, user_email = register_user(email=f"user1@test_post_project_state_invalid_state_id.com", name="user1")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_post_project_state_invalid_state_id",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_post_project_state_invalid_state_id",
        institution="test_post_project_state_invalid_state_id",
        associated_users_emails=[],
        name="test_post_project_state_invalid_state_id",
        filter_set_ids=[filter_set_id]
    ).json["id"]
    assert admin_update_project_state_post(
        authorization_token=admin_user[0],
        project_id=project_id,
        state_id=999999,  # Assuming this state ID does not exist
        status_code=404
    )

def test_post_project_state_invalid_project_id(register_user, login, filter_set_post, project_post, admin_user, admin_update_project_state_post, admin_states_get):
    user_id, user_email = register_user(email=f"user1@test_post_project_state_invalid_project_id.com", name="user1")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_post_project_state_invalid_project_id",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_post_project_state_invalid_project_id",
        institution="test_post_project_state_invalid_project_id",
        associated_users_emails=[],
        name="test_post_project_state_invalid_project_id",
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
        project_id=999999,  # Assuming this project ID does not exist
        state_id=state_id,
        status_code=404
    )

def test_post_project_state_no_state_change(register_user, login, filter_set_post, project_post, admin_user, admin_update_project_state_post, admin_states_get):
    user_id, user_email = register_user(email=f"user1@test_post_project_state_no_state_change.com", name="user1")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_post_project_state_no_state_change",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_post_project_state_no_state_change",
        institution="test_post_project_state_no_state_change",
        associated_users_emails=[],
        name="test_post_project_state_no_state_change",
        filter_set_ids=[filter_set_id]
    ).json["id"]
    states = admin_states_get(
        authorization_token=user_id,
        status_code=200
    )
    for state in states.json:
        if state["code"] == "APPROVED":
            state_id = state["id"]
    # First state change to APPROVED
    assert admin_update_project_state_post(
        authorization_token=admin_user[0],
        project_id=project_id,
        state_id=state_id,
        status_code=200
    )
    # Second state change to the same state, should result in no change
    assert admin_update_project_state_post(
        authorization_token=admin_user[0],
        project_id=project_id,
        state_id=state_id,
        status_code=200
    )

def test_post_project_state_block_change_when_in_final_state(register_user, login, filter_set_post, project_post, admin_user, admin_update_project_state_post, admin_states_get):
    user_id, user_email = register_user(email=f"user1@test_post_project_state_block_change_when_in_final_state.com", name="user1")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_post_project_state_block_change_when_in_final_state",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_post_project_state_block_change_when_in_final_state",
        institution="test_post_project_state_block_change_when_in_final_state",
        associated_users_emails=[],
        name="test_post_project_state_block_change_when_in_final_state",
        filter_set_ids=[filter_set_id]
    ).json["id"]
    states = admin_states_get(
        authorization_token=user_id,
        status_code=200
    )
    for state in states.json:
        if state["code"] == "REJECTED":
            state_id = state["id"]
    # First state change to REJECTED
    assert admin_update_project_state_post(
        authorization_token=admin_user[0],
        project_id=project_id,
        state_id=state_id,
        status_code=200
    )
    for state in states.json:
        if state["code"] == "APPROVED":
            state_id = state["id"]
    # Attempt to change state again when already in final state, should be blocked
    assert admin_update_project_state_post(
        authorization_token=admin_user[0],
        project_id=project_id,
        state_id=state_id,
        status_code=400
    )

def test_attempt_to_move_project_to_deprecated_state(session, register_user, login, filter_set_post, project_post, admin_user, admin_update_project_state_post, admin_states_get):
    user_id, user_email = register_user(email=f"user1@test_attempt_to_move_project_to_deprecated_state.com", name="user1")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_attempt_to_move_project_to_deprecated_state",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_attempt_to_move_project_to_deprecated_state",
        institution="test_attempt_to_move_project_to_deprecated_state",
        associated_users_emails=[],
        name="test_attempt_to_move_project_to_deprecated_state",
        filter_set_ids=[filter_set_id]
    ).json["id"]
    deprecated_id = session.query(State).filter(State.code == "DEPRECATED").first().id
    assert admin_update_project_state_post(
        authorization_token=admin_user[0],
        project_id=project_id,
        state_id=deprecated_id,
        status_code=400
    )

def test_move_project_to_data_available_requires_approved_url(register_user, login, filter_set_post, project_post, admin_user, admin_update_project_state_post, admin_states_get):
    user_id, user_email = register_user(email=f"user1@test_move_project_to_data_available_requires_approved_url.com", name="user1")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_move_project_to_data_available_requires_approved_url",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_move_project_to_data_available_requires_approved_url",
        institution="test_move_project_to_data_available_requires_approved_url",
        associated_users_emails=[],
        name="test_move_project_to_data_available_requires_approved_url",
        filter_set_ids=[filter_set_id]
    ).json["id"]

    states = admin_states_get(
        authorization_token=user_id,
        status_code=200
    )
    for state in states.json:
        if state["code"] == "DATA_AVAILABLE":
            state_id = state["id"]
    # First state change to DATA_AVAILABLE
    assert admin_update_project_state_post(
        authorization_token=admin_user[0],
        project_id=project_id,
        state_id=state_id,
        status_code=400
    )

def test_move_project_to_data_available_fails_due_to_consortium_list(register_user, login, filter_set_post, project_post, admin_user, admin_update_project_state_post, admin_states_get, admin_update_project_put, admin_update_associated_user_role):
    user_id, user_email = register_user(email=f"user1@test_move_project_to_data_available_fails_due_to_consortium_list.com", name="user1")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_move_project_to_data_available_fails_due_to_consortium_list",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_move_project_to_data_available_fails_due_to_consortium_list",
        institution="test_move_project_to_data_available_fails_due_to_consortium_list",
        associated_users_emails=[],
        name="test_move_project_to_data_available_fails_due_to_consortium_list",
        filter_set_ids=[filter_set_id]
    ).json["id"]

    states = admin_states_get(
        authorization_token=user_id,
        status_code=200
    )
    for state in states.json:
        if state["code"] == "DATA_AVAILABLE":
            state_id = state["id"]
    # First state change to DATA_AVAILABLE
    assert admin_update_project_state_post(
        authorization_token=admin_user[0],
        project_id=project_id,
        state_id=state_id,
        input_consortium_codes=["INSTRUCT"],
        status_code=400
    )


def test_move_project_to_data_available(register_user, login, filter_set_post, project_post, admin_user, admin_update_project_state_post, admin_states_get, admin_update_project_put, admin_update_associated_user_role, register_user_who_will_recieve_emails):
    user_id, user_email = register_user_who_will_recieve_emails[0]
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_move_project_to_data_available",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_move_project_to_data_available",
        institution="test_move_project_to_data_available",
        associated_users_emails=[],
        name="test_move_project_to_data_available",
        filter_set_ids=[filter_set_id]
    ).json["id"]

    admin_update_project_put(
        authorization_token=admin_user[0],
        project_id=project_id,
        approved_url="http://approved.url",
        status_code=200
    )
    assert admin_update_associated_user_role(
        authorization_token=admin_user[0],
        user_id=user_id,
        project_id=project_id,
        role="DATA_ACCESS",
        status_code=200
    )  

    states = admin_states_get(
        authorization_token=user_id,
        status_code=200
    )
    for state in states.json:
        if state["code"] == "DATA_AVAILABLE":
            state_id = state["id"]
    # First state change to DATA_AVAILABLE without consortium list
    assert admin_update_project_state_post(
        authorization_token=admin_user[0],
        project_id=project_id,
        state_id=state_id,
        status_code=200
    )

def test_move_project_to_data_available_already_in_data_available_state(register_user, login, filter_set_post, project_post, admin_user, admin_update_project_state_post, admin_states_get, admin_update_project_put, admin_update_associated_user_role, register_user_who_will_recieve_emails, patch_ses_client):
    patch_ses_client()
    user_id, user_email = register_user_who_will_recieve_emails[0]
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_move_project_to_data_available_already_in_data_available_state",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_move_project_to_data_available_already_in_data_available_state",
        institution="test_move_project_to_data_available_already_in_data_available_state",
        associated_users_emails=[],
        name="test_move_project_to_data_available_already_in_data_available_state",
        filter_set_ids=[filter_set_id]
    ).json["id"]

    admin_update_project_put(
        authorization_token=admin_user[0],
        project_id=project_id,
        approved_url="http://approved.url",
        status_code=200
    )
    assert admin_update_associated_user_role(
        authorization_token=admin_user[0],
        user_id=user_id,
        project_id=project_id,
        role="DATA_ACCESS",
        status_code=200
    )  

    states = admin_states_get(
        authorization_token=user_id,
        status_code=200
    )
    for state in states.json:
        if state["code"] == "DATA_AVAILABLE":
            state_id = state["id"]
    # First state change to DATA_AVAILABLE without consortium list
    assert admin_update_project_state_post(
        authorization_token=admin_user[0],
        project_id=project_id,
        state_id=state_id,
        status_code=200
    )
    assert admin_update_project_state_post(
        authorization_token=admin_user[0],
        project_id=project_id,
        state_id=state_id,
        status_code=400
    )