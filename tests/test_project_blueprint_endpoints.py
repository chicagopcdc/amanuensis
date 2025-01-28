import pytest



def test_user_creates_project_success(
                              login, 
                              register_user, 
                              project_post,
                              filter_set_post
                              ):

    user_id, user_email =  register_user(email=f"user_1@test_user_creates_project.com", name="test_user")
    login(user_id, user_email)

    filter_set_id = filter_set_post(
        user_id, 
        name="test_user_creates_project", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]

    assert project_post(
        authorization_token=user_id, 
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_user_creates_project",
        institution="test_user_creates_project",
        associated_users_emails=["user_2@test_user_creates_project.com"],
        name="test_user_creates_project", 
        filter_set_ids=[filter_set_id]
    )

def test_user_creates_project_bad_parameters( 
                              login, 
                              register_user, 
                              project_post,
                              filter_set_post
                              ):

    user_id, user_email =  register_user(email=f"user_1@test_user_creates_project_bad_parameters.com", name="test_user")
    login(user_id, user_email)

    filter_set_id = filter_set_post(
        user_id, 
        name="test_user_creates_project_bad_parameters", 
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]

    assert project_post(
        authorization_token=user_id, 
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_user_creates_project",
        institution="test_user_creates_project",
        associated_users_emails=["user_2@test_user_creates_project.com"],
        filter_set_ids=[filter_set_id],
        status_code=400
    )
