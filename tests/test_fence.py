import pytest
from amanuensis.resources.fence import fence_get_users
from amanuensis.config import config

def test_fence_requests(client, register_user, mock_requests_post, patch_auth_header):
    mock_requests_post()
    user_id, user_email = register_user(email=f"admin@test_fence_requests.edu", name="test_fence_requests", role="admin")
    patch_auth_header(str(user_id))
    response = fence_get_users(ids=[user_id])
    assert response['users'][0]['id'] == user_id
    response = fence_get_users(usernames=["admin@test_fence_requests.edu"])
    assert response['users'][0]['id'] == user_id
    response = fence_get_users(usernames=["doesnotexist@test.com"])
    assert len(response['users']) == 0
    response = fence_get_users(usernames=[None])
    assert len(response['users']) == 0


def test_get_fence_users_via_endpoint(client, register_user, fence_users, mock_requests_get):
    admin_id, admin_email = register_user(email=f"admin@test_get_fence_users_via_endpoint.edu", name="test_get_fence_users_via_endpoint", role="admin")
    mock_requests_get()
    response = client.get('/admin/get_users', headers={"Authorization": f'bearer {admin_id}'})
    assert response.status_code == 200
    assert len(response.json['users']) == len(fence_users)

def test_get_fence_users_via_endpoint_no_auth(client, register_user, mock_requests_get):
    #user does not have amanuensis access return 403 to client
    user_id, user_email = register_user(email=f"user@test_get_fence_users_via_endpoint_no_auth.edu", name="test_get_fence_users_via_endpoint_no_auth", role="user")
    mock_requests_get()
    response = client.get('/admin/get_users', headers={"Authorization": f'bearer {user_id}'})
    assert response.status_code == 403
    assert response.json == None

def test_get_users_via_endpoint_service_auth_fails(client, register_user, mock_requests_get):
    #this would happen if one of the RSA keys was missing in either amanuensis or fence
    #or for some reason pcdcutils is rejecting amanuensis request
    admin_id, admin_email = register_user(email=f"admin@test_get_users_via_endpoint_service_auth_fails.edu", name="test_get_users_via_endpoint_service_auth_fails", role="admin")
    mock_requests_get(urls={f"{config['FENCE']}/admin/users": 401})
    response = client.get('/admin/get_users', headers={"Authorization": f'bearer {admin_id}'})
    assert response.status_code == 500
    assert response.json == None
