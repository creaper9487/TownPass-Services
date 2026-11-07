from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_example_crud():
    res = client.post("/api/examples", json={"name": "foo"})
    assert res.status_code == 201
    item = res.json()["data"]
    assert item["name"] == "foo"

    res = client.get(f"/api/examples/{item['id']}")
    assert res.json()["data"] == item

    res = client.get("/api/examples/9999")
    assert res.status_code == 404
    assert res.json()["success"] is False
