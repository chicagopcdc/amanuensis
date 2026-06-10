from unittest.mock import MagicMock, patch


def test_export_project_success(register_user, login, filter_set_post, project_post, admin_user, client):
    user_id, user_email = register_user(email=f"user_1@test_export_project_success.com", name=__name__)
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_export_project_success",
        filter_object={"consortium": {"__type": "OPTION", "selectedValues": ["INSTRUCT", "INRG"], "isExclusion": False}},
        graphql_object={"AND": [{"IN": {"consortium": ["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_export_project_success",
        institution="test_export_project_success",
        associated_users_emails=[],
        name="test_export_project_success",
        filter_set_ids=[filter_set_id]
    ).json["id"]

    mocked_response = MagicMock()
    mocked_response.status_code = 200
    mocked_response.json = MagicMock(return_value={"uid": "fake-job-uid"})

    with patch("amanuensis.resources.sower.requests.post", return_value=mocked_response) as mock_post:
        response = client.post(
            f"/admin/project/export/{project_id}",
            headers={"Authorization": f'bearer {admin_user[0]}'}
        )

    assert response.status_code == 200
    assert response.json["project_id"] == str(project_id)
    assert isinstance(response.json["search_id"], int)
    assert response.json["job_uid"] == "fake-job-uid"
    assert mock_post.called


def test_export_project_fail_user_not_admin(register_user, login, filter_set_post, project_post, client):
    user_id, user_email = register_user(email=f"user_1@test_export_project_fail_user_not_admin.com", name=__name__)
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_export_project_fail_user_not_admin",
        filter_object={"consortium": {"__type": "OPTION", "selectedValues": ["INSTRUCT", "INRG"], "isExclusion": False}},
        graphql_object={"AND": [{"IN": {"consortium": ["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_export_project_fail_user_not_admin",
        institution="test_export_project_fail_user_not_admin",
        associated_users_emails=[],
        name="test_export_project_fail_user_not_admin",
        filter_set_ids=[filter_set_id]
    ).json["id"]

    response = client.post(
        f"/admin/project/export/{project_id}",
        headers={"Authorization": f'bearer {user_id}'}
    )

    assert response.status_code == 403

def test_export_project_fail_sower_error(register_user, login, filter_set_post, project_post, admin_user, client):
    user_id, user_email = register_user(email=f"user_1@test_export_project_fail_sower_error.com", name=__name__)
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_export_project_fail_sower_error",
        filter_object={"consortium": {"__type": "OPTION", "selectedValues": ["INSTRUCT", "INRG"], "isExclusion": False}},
        graphql_object={"AND": [{"IN": {"consortium": ["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_export_project_fail_sower_error",
        institution="test_export_project_fail_sower_error",
        associated_users_emails=[],
        name="test_export_project_fail_sower_error",
        filter_set_ids=[filter_set_id]
    ).json["id"]

    mocked_response = MagicMock()
    mocked_response.status_code = 500
    mocked_response.text = "INTERNAL SERVER ERROR"

    with patch("amanuensis.resources.sower.requests.post", return_value=mocked_response):
        response = client.post(
            f"/admin/project/export/{project_id}",
            headers={"Authorization": f'bearer {admin_user[0]}'}
        )

    assert response.status_code == 500
