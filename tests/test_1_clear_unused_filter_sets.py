import pytest
from amanuensis.errors import NotFound, UserError
from amanuensis.models import Search, SearchIsShared, ProjectSearch
from amanuensis.scripting.clear_old_filter_sets import main




def test_clear_unused_filter_sets(session, client, register_user, login, mock_requests_post, pytestconfig):
    # Validate initial state
    # User creates filter-set via UI and has user_id
    # User creates project, and a new search without a user_id is created and added to project_has_search
    # User creates snapshot, and a new search without a user_id is created and added to search_is_shared
    user_id, user_email = register_user(email=f"user_1@{__name__}.com", name=__name__)
    user_id_2, user_email_2 = register_user(email=f"user_2@{__name__}.com", name=__name__)
    admin_id, admin_email = register_user(email=f"admin@{__name__}", name=__name__, role="admin")

    login(user_id, user_email)

    search_1_response = client.post(
        "/filter-sets?explorerId=1",
        json={"name": f"search_1_{__name__}"},
        headers={"Authorization": f'bearer {user_id}'},
    )
    assert search_1_response.status_code == 200
    search_1_id = search_1_response.json["id"]

    search_2_response = client.post(
        "/filter-sets?explorerId=1",
        json={"name": f"search_2_{__name__}"},
        headers={"Authorization": f'bearer {user_id}'},
    )
    assert search_2_response.status_code == 200
    search_2_id = search_2_response.json["id"]

    login(user_id_2, user_email_2)

    search_3_response = client.post(
        "/filter-sets?explorerId=1",
        json={"name": f"search_3_{__name__}"},
        headers={"Authorization": f'bearer {user_id_2}'},
    )
    assert search_3_response.status_code == 200
    search_3_id = search_3_response.json["id"]

    login(user_id, user_email)

    snapshot_response = client.post(
        "filter-sets/snapshot",
        json={"filterSetId": search_1_id},
        headers={"Authorization": f'bearer {user_id}'},
    )
    assert snapshot_response.status_code == 200

    login(admin_id, admin_email)
    mock_requests_post(consortiums=["INSTRUCT", "INRG"])
    project_response = client.post(
        f"/admin/projects",
        json={
            "user_id": user_id,
            "name": f"{__name__}_project",
            "description": "This is an endpoint test project",
            "institution": "test university",
            "filter_set_ids": [search_2_id],
            "associated_users_emails": [],
        },
        headers={"Authorization": f'bearer {admin_id}'},
    )
    assert project_response.status_code == 200
    project_id = project_response.json["id"]

    assert session.query(Search).count() == 5
    assert session.query(Search).filter(Search.user_id.is_(None)).count() == 2
    assert session.query(SearchIsShared).count() == 1
    assert session.query(ProjectSearch).count() == 1

    # Run main function
    main(pytestconfig.getoption("--configuration-file"))

    # Validate post-main state
    assert session.query(Search).count() == 5
    assert session.query(Search).filter(Search.user_id.is_(None)).count() == 2
    assert session.query(SearchIsShared).count() == 1
    assert session.query(ProjectSearch).count() == 1

    #change filter-set in project
    admin_copy_search_to_project_json = {
        "filtersetId": search_3_id,
        "projectId": project_id
    }
    admin_copy_search_to_project_response = client.post("admin/copy-search-to-project", json=admin_copy_search_to_project_json, headers={"Authorization": f'bearer {admin_id}'})
    assert session.query(Search).count() == 6
    assert session.query(Search).filter(Search.user_id.is_(None)).count() == 3
    assert session.query(SearchIsShared).count() == 1
    assert session.query(ProjectSearch).count() == 1

    main(pytestconfig.getoption("--configuration-file"))

    assert session.query(Search).count() == 5
    assert session.query(Search).filter(Search.user_id.is_(None)).count() == 2
    assert session.query(SearchIsShared).count() == 1
    assert session.query(ProjectSearch).count() == 1

    deleted_filter_set = session.query(Search).filter(Search.name == "test_1_clear_unused_filter_sets_project_search_2_test_1_clear_unused_filter_sets").first()
    assert not deleted_filter_set