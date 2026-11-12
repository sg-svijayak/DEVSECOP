import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr("app.main.DB_PATH", str(tmp_path / "t.db"))
    from app.main import app
    return TestClient(app)


def test_health(client):
    assert client.get("/healthz").json() == {"status": "ok"}


def test_crud(client):
    r = client.post("/api/todos", json={"title": "  write tests "})
    assert r.status_code == 201
    todo = r.json()
    assert todo["title"] == "write tests" and todo["done"] is False

    assert len(client.get("/api/todos").json()) == 1

    r = client.patch(f"/api/todos/{todo['id']}", json={"done": True})
    assert r.json()["done"] is True

    assert client.delete(f"/api/todos/{todo['id']}").status_code == 204
    assert client.get("/api/todos").json() == []


def test_validation(client):
    assert client.post("/api/todos", json={"title": ""}).status_code == 422
    assert client.post("/api/todos", json={"title": "x" * 201}).status_code == 422


def test_not_found(client):
    assert client.patch("/api/todos/999", json={"done": True}).status_code == 404
    assert client.delete("/api/todos/999").status_code == 404
