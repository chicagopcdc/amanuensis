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
    assert len(response.json["search_ids"]) == 1
    assert isinstance(response.json["search_ids"][0], int)
    assert response.json["job_uid"] == "fake-job-uid"
    assert mock_post.called


def test_export_project_with_multiple_filter_sets_exports_all_of_them(
    register_user, login, filter_set_post, project_post, admin_user, client
):
    """
    A project can have more than one associated search. Every one of them has to
    reach the export job - the job unions them into a single cohort - rather
    than the first one being exported and the rest silently dropped.
    """
    user_id, user_email = register_user(
        email=f"user_1@test_export_project_multiple.com", name=__name__
    )
    login(user_id, user_email)

    first_filter_set_id = filter_set_post(
        user_id,
        name="test_export_project_multiple_1",
        filter_object={"consortium": {"__type": "OPTION", "selectedValues": ["INRG"], "isExclusion": False}},
        graphql_object={"AND": [{"IN": {"consortium": ["INRG"]}}]}
    ).json["id"]
    second_filter_set_id = filter_set_post(
        user_id,
        name="test_export_project_multiple_2",
        filter_object={"consortium": {"__type": "OPTION", "selectedValues": ["INSTRUCT"], "isExclusion": False}},
        graphql_object={"AND": [{"IN": {"consortium": ["INSTRUCT"]}}]}
    ).json["id"]

    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_export_project_multiple",
        institution="test_export_project_multiple",
        associated_users_emails=[],
        name="test_export_project_multiple",
        filter_set_ids=[first_filter_set_id, second_filter_set_id]
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
    assert len(response.json["search_ids"]) == 2

    dispatched_input = mock_post.call_args.kwargs["json"]["input"]

    # both filter sets are sent to the job...
    assert len(dispatched_input["filters"]) == 2
    assert {"AND": [{"IN": {"consortium": ["INRG"]}}]} in dispatched_input["filters"]
    assert {"AND": [{"IN": {"consortium": ["INSTRUCT"]}}]} in dispatched_input["filters"]

    # ...and the single-search key still carries the first one, so this keeps
    # working against a pelican image that predates multi-search support
    assert dispatched_input["filter"] == dispatched_input["filters"][0]


def test_export_project_orders_filter_sets_deterministically(
    register_user, login, filter_set_post, project_post, admin_user, client
):
    """
    The order of the filter sets decides the order of the exported cohort, so
    two exports of an unchanged project must dispatch the same payload.
    """
    user_id, user_email = register_user(
        email=f"user_1@test_export_project_order.com", name=__name__
    )
    login(user_id, user_email)

    filter_set_ids = [
        filter_set_post(
            user_id,
            name=f"test_export_project_order_{i}",
            filter_object={"consortium": {"__type": "OPTION", "selectedValues": ["INRG"], "isExclusion": False}},
            graphql_object={"AND": [{"IN": {"consortium": ["INRG"]}}, {"IN": {"sex": [f"value_{i}"]}}]}
        ).json["id"]
        for i in range(3)
    ]

    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INRG"],
        description="test_export_project_order",
        institution="test_export_project_order",
        associated_users_emails=[],
        name="test_export_project_order",
        filter_set_ids=filter_set_ids
    ).json["id"]

    mocked_response = MagicMock()
    mocked_response.status_code = 200
    mocked_response.json = MagicMock(return_value={"uid": "fake-job-uid"})

    dispatched = []
    for _ in range(2):
        with patch("amanuensis.resources.sower.requests.post", return_value=mocked_response) as mock_post:
            response = client.post(
                f"/admin/project/export/{project_id}",
                headers={"Authorization": f'bearer {admin_user[0]}'}
            )
        assert response.status_code == 200
        dispatched.append(mock_post.call_args.kwargs["json"]["input"]["filters"])

    assert len(dispatched[0]) == 3
    assert dispatched[0] == dispatched[1]


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
