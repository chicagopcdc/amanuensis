import pytest

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
