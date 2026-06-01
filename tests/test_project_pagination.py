import re
from urllib.parse import parse_qs, urlparse

import pytest

from amanuensis.resources.userdatamodel.project import create_project

NUM_PROJECTS = 5
PER_PAGE = 2


@pytest.fixture(scope="module", autouse=True)
def s3():
    """Override conftest s3; pagination tests do not use AWS."""
    yield None


@pytest.fixture(scope="module")
def pagination_setup(session, register_user):
    admin_id, admin_email = register_user(
        email=f"admin@{__name__}.com",
        name=__name__,
        role="admin",
    )
    for i in range(NUM_PROJECTS):
        create_project(
            session,
            admin_id,
            f"pagination test project {i}",
            f"pag_project_{i}",
            "test_institution",
        )
    session.commit()
    return {
        "admin_id": admin_id,
        "admin_email": admin_email,
    }


def _projects_url(page, per_page, special_user_admin=True):
    query = f"page={page}&per_page={per_page}"
    if special_user_admin:
        query += "&special_user=admin"
    return f"/projects?{query}"


def _get_projects(client, token, page=1, per_page=PER_PAGE):
    return client.get(
        _projects_url(page, per_page),
        headers={"Authorization": f"bearer {token}"},
    )


def _parse_link_rel(link_header, rel):
    if not link_header:
        return None
    match = re.search(rf'<([^>]+)>;\s*rel="{rel}"', link_header)
    return match.group(1) if match else None


def _get_via_link(client, token, link_url):
    """Follow a Link URL (path + query, as returned by build_link_header)."""
    parsed = urlparse(link_url)
    path = parsed.path or link_url.split("?")[0]
    if parsed.query:
        path = f"{path}?{parsed.query}"
    return client.get(path, headers={"Authorization": f"bearer {token}"})


def _page_from_link(link_url):
    return int(parse_qs(urlparse(link_url).query)["page"][0])


def _project_ids(response):
    return {project["id"] for project in response.get_json()}


@pytest.mark.order(1)
def test_pagination_respects_per_page_size(
    client, login, mock_requests_post, pagination_setup
):
    mock_requests_post()
    login(pagination_setup["admin_id"], pagination_setup["admin_email"])

    response = _get_projects(client, pagination_setup["admin_id"], page=1, per_page=PER_PAGE)

    assert response.status_code == 200
    assert len(response.get_json()) == PER_PAGE


@pytest.mark.order(2)
def test_pagination_next_page(client, login, mock_requests_post, pagination_setup):
    mock_requests_post()
    login(pagination_setup["admin_id"], pagination_setup["admin_email"])

    first_page = _get_projects(client, pagination_setup["admin_id"], page=1, per_page=PER_PAGE)
    second_page = _get_projects(client, pagination_setup["admin_id"], page=2, per_page=PER_PAGE)

    assert first_page.status_code == 200
    assert second_page.status_code == 200

    first_ids = _project_ids(first_page)
    second_ids = _project_ids(second_page)

    assert len(first_ids) == PER_PAGE
    assert len(second_ids) == PER_PAGE
    assert first_ids.isdisjoint(second_ids)

    link = first_page.headers.get("Link")
    assert link is not None
    next_url = _parse_link_rel(link, "next")
    assert next_url is not None
    assert _page_from_link(next_url) == 2

    via_link = _get_via_link(client, pagination_setup["admin_id"], next_url)
    assert via_link.status_code == 200
    assert _project_ids(via_link) == second_ids

    prev_url = _parse_link_rel(second_page.headers.get("Link"), "prev")
    assert prev_url is not None
    assert _page_from_link(prev_url) == 1

    via_prev = _get_via_link(client, pagination_setup["admin_id"], prev_url)
    assert via_prev.status_code == 200
    assert _project_ids(via_prev) == first_ids
    assert _parse_link_rel(first_page.headers.get("Link"), "prev") is None

    # GitHub-style Link header on a middle page: first, prev, next, last
    middle_link = second_page.headers.get("Link")
    for rel in ("first", "prev", "next", "last"):
        assert _parse_link_rel(middle_link, rel) is not None
    assert _page_from_link(_parse_link_rel(middle_link, "first")) == 1
    assert _page_from_link(_parse_link_rel(middle_link, "last")) == 3
