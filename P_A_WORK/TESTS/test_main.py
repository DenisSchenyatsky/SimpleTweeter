from fastapi.testclient import TestClient
import requests as client

id_arr = []


def test_get_empty_user():
    response = client.get(
        "http://127.0.0.1:80/api/users/123",
        headers={"X-Token": "coneofsilence"},
    )
    assert response.status_code == 404
    
def test_get_testuser():
    response = client.get(
        "http://127.0.0.1:80/api/users/1",
        headers={"X-Token": "coneofsilence"},
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data.get("user").get("name") == "Test User"
