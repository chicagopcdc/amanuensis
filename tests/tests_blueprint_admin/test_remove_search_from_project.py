import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture(scope="module", autouse=True)
def s3(app_instance):
    """
    Nothing here touches s3, so override the conftest fixture that reaches out to
    a real bucket.
    """
    mock_s3_client = MagicMock()
    mock_s3_client.create_bucket.return_value = None
    mock_s3_client.list_buckets.return_value = {'Buckets': []}
    mock_s3_client.delete_object.return_value = None
    mock_s3_client.list_objects_v2.return_value = {'Contents': []}

    with patch.object(app_instance.s3_boto, 's3_client', mock_s3_client):
        yield mock_s3_client


@pytest.fixture(scope="function")
def admin_remove_search_from_project(client, mock_requests_post):
    def route_admin_remove_search_from_project(authorization_token,
                                               project_id=None,
                                               search_ids=None,
                                               consortiums_to_be_returned_from_pcdc_analysis_tools=[],
                                               status_code=200):
        # removal re-runs request reconciliation against the searches that remain
        mock_requests_post(consortiums=consortiums_to_be_returned_from_pcdc_analysis_tools)
        json = {}
        if project_id is not None:
            json["projectId"] = project_id
        if search_ids is not None:
            json["searchIds"] = search_ids

        response = client.delete(
            "/admin/remove-search-from-project",
            json=json,
            headers={"Authorization": f'bearer {authorization_token}'},
        )
        assert response.status_code == status_code
        return response

    return route_admin_remove_search_from_project


def _filter_set(filter_set_post, user_id, name, consortium):
    return filter_set_post(
        user_id,
        name=name,
        filter_object={"consortium":{"__type":"OPTION","selectedValues":[consortium],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":[consortium]}}]}
    ).json["id"]


def _project_searches(session, project_id):
    """The project's own copies of its searches, keyed by name."""
    from amanuensis.models import ProjectSearch

    return {
        project_search.search.name: project_search.search.id
        for project_search in session.query(ProjectSearch).filter(ProjectSearch.project_id == project_id)
    }


def _live_consortiums(session, project_id):
    from amanuensis.resources.userdatamodel.request_has_state import get_request_states

    return {
        request_state.request.consortium_data_contributor.code
        for request_state in get_request_states(session, project_id=project_id, filter_out_depricated=True, latest=True)
    }


def _two_search_project(register_user, login, filter_set_post, project_post, admin_copy_search_to_project, admin_user, test_name):
    """
    A project holding an INRG search and an INSTRUCT search, so each consortium
    has a live request. Returns the project id.
    """
    user_id, user_email = register_user(email=f"user_1@{test_name}.com", name=__name__)
    login(user_id, user_email)

    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INRG"],
        description=test_name,
        institution=test_name,
        associated_users_emails=[],
        name=test_name,
        filter_set_ids=[_filter_set(filter_set_post, user_id, f"{test_name}_inrg", "INRG")]
    ).json["id"]

    instruct_id = _filter_set(filter_set_post, user_id, f"{test_name}_instruct", "INSTRUCT")

    login(admin_user[0], admin_user[1])
    assert admin_copy_search_to_project(
        authorization_token=admin_user[0],
        filter_set_id=instruct_id,
        project_id=project_id,
        mode="add",
        expected_search_count=2,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INRG", "INSTRUCT"]
    )

    return project_id


def test_remove_search_from_project(register_user, login, filter_set_post, project_post, admin_copy_search_to_project, admin_remove_search_from_project, admin_user, session):
    """
    Removing a search takes it off the project and deprecates the request for a
    consortium no remaining search covers, while the other request stays live.
    """
    test_name = "test_remove_search_from_project"
    project_id = _two_search_project(register_user, login, filter_set_post, project_post, admin_copy_search_to_project, admin_user, test_name)

    searches = _project_searches(session, project_id)
    assert _live_consortiums(session, project_id) == {"INRG", "INSTRUCT"}

    instruct_copy = searches[f"{test_name}_{test_name}_instruct"]
    inrg_copy = searches[f"{test_name}_{test_name}_inrg"]

    admin_remove_search_from_project(
        authorization_token=admin_user[0],
        project_id=project_id,
        search_ids=[instruct_copy],
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INRG"],
    )

    session.expire_all()
    assert set(_project_searches(session, project_id).values()) == {inrg_copy}
    assert _live_consortiums(session, project_id) == {"INRG"}


def test_remove_last_search_is_refused(register_user, login, filter_set_post, project_post, admin_copy_search_to_project, admin_remove_search_from_project, admin_user, session):
    test_name = "test_remove_last_search_is_refused"
    project_id = _two_search_project(register_user, login, filter_set_post, project_post, admin_copy_search_to_project, admin_user, test_name)

    admin_remove_search_from_project(
        authorization_token=admin_user[0],
        project_id=project_id,
        search_ids=list(_project_searches(session, project_id).values()),
        status_code=400,
    )

    session.expire_all()
    assert len(_project_searches(session, project_id)) == 2


def test_remove_search_not_on_project_is_refused(register_user, login, filter_set_post, project_post, admin_copy_search_to_project, admin_remove_search_from_project, admin_user, session):
    """
    The ids are the project's own copies; a filter set the project was built
    from is a different row and is not on the project.
    """
    test_name = "test_remove_search_not_on_project_is_refused"
    project_id = _two_search_project(register_user, login, filter_set_post, project_post, admin_copy_search_to_project, admin_user, test_name)

    on_project = set(_project_searches(session, project_id).values())
    not_on_project = max(on_project) + 1000

    admin_remove_search_from_project(
        authorization_token=admin_user[0],
        project_id=project_id,
        search_ids=[not_on_project],
        status_code=400,
    )

    session.expire_all()
    assert set(_project_searches(session, project_id).values()) == on_project


def test_remove_search_missing_parameters(register_user, login, filter_set_post, project_post, admin_copy_search_to_project, admin_remove_search_from_project, admin_user, session):
    test_name = "test_remove_search_missing_parameters"
    project_id = _two_search_project(register_user, login, filter_set_post, project_post, admin_copy_search_to_project, admin_user, test_name)
    search_id = next(iter(_project_searches(session, project_id).values()))

    admin_remove_search_from_project(authorization_token=admin_user[0], search_ids=[search_id], status_code=400)
    admin_remove_search_from_project(authorization_token=admin_user[0], project_id=project_id, status_code=400)
    admin_remove_search_from_project(authorization_token=admin_user[0], project_id=project_id, search_ids=["1"], status_code=400)


def test_remove_search_requires_admin(register_user, login, filter_set_post, project_post, admin_copy_search_to_project, admin_remove_search_from_project, admin_user, session):
    test_name = "test_remove_search_requires_admin"
    project_id = _two_search_project(register_user, login, filter_set_post, project_post, admin_copy_search_to_project, admin_user, test_name)
    search_id = next(iter(_project_searches(session, project_id).values()))

    user_id, user_email = register_user(email=f"user_2@{test_name}.com", name=__name__)
    login(user_id, user_email)

    admin_remove_search_from_project(
        authorization_token=user_id,
        project_id=project_id,
        search_ids=[search_id],
        status_code=403,
    )
