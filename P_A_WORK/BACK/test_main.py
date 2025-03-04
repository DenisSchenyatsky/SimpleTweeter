from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

id_arr = []


def test_create_recipe():
    response = client.get(
        "/api/users/123",
        headers={"X-Token": "coneofsilence"},
    )
    assert response.status_code == 200
    response_data = response.json()


# def test_read_all_recipes():
#     response = client.get("/recipes", headers={"X-Token": "coneofsilence"})
#     assert response.status_code == 200
#     response_data = response.json()
#     assert isinstance(response_data, list)

#     for d in response_data:
#         assert isinstance(d, dict)
#         assert isinstance(d["id"], int)
#         assert isinstance(d["name"], str)
#         assert isinstance(d["watched_count"], int)
#         assert isinstance(d["time_spent"], str)
#         id_arr.append(d["id"])


# def test_read_recipes_by_one():
#     for idx in id_arr:
#         response = client.get(f"/recipes{idx}", headers={"X-Token": "coneofsilence"})
#         assert response.status_code == 200
#         d = response.json()
#         assert isinstance(d, dict)
#         assert isinstance(d["name"], str)
#         assert isinstance(d["time_spent"], str)
#         assert isinstance(d["description"], str)
#         assert isinstance(d["products"], list)
#         for d2 in d["products"]:
#             assert isinstance(d2["name"], str)
#             assert isinstance(d2["id"], int)
