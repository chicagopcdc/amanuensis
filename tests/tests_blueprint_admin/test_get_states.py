def test_get_states_as_admin_success(admin_user, admin_states_get):
    codes = [ "IN_REVIEW", "REJECTED", "APPROVED", "DRAFT", "SUBMITTED", "REVISION", "APPROVED_WITH_FEEDBACK",
              "REQUEST_CRITERIA_FINALIZED", "WITHDRAWAL", "AGREEMENTS_NEGOTIATION", "AGREEMENTS_EXECUTED", "DATA_DOWNLOADED", "PUBLISHED", "DATA_AVAILABLE"]
    assert admin_states_get(
        authorization_token=admin_user[0],
        states_list=codes,
        status_code=200
    )

def test_get_states_as_non_admin_success(register_user, login, admin_states_get):
    codes = [ "IN_REVIEW", "REJECTED", "APPROVED", "DRAFT", "SUBMITTED", "REVISION", "APPROVED_WITH_FEEDBACK",
              "REQUEST_CRITERIA_FINALIZED", "WITHDRAWAL", "AGREEMENTS_NEGOTIATION", "AGREEMENTS_EXECUTED", "DATA_DOWNLOADED", "PUBLISHED", "DATA_AVAILABLE"]
    user_id, user_email = register_user(email=f"user1@test_get_states_as_non_admin_success.com", name="user1")
    login(user_id, user_email)
    assert admin_states_get(
        authorization_token=user_id,
        states_list=codes,
        status_code=200
    )

