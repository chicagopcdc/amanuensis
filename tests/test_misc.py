def test_status(client):
    response = client.get("/_status")
    assert response.status_code == 200

def test_version(client):
    response = client.get("/_version")
    assert response.status_code == 200