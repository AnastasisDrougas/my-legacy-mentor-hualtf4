
import pytest
from fastapi.testclient import TestClient

from app import database
from app.main import app
from app.repositories.conversations import add_message

client = TestClient(app)


@pytest.fixture(autouse=True)
def temporary_database(tmp_path, monkeypatch):
    # Use an isolated database for each test
    db_path = tmp_path / "conversations_api.db"

    monkeypatch.setattr(
        database,
        "get_database_path",
        lambda: db_path,
    )

    database.init_db()


def test_create_conversation_api():
    response = client.post("/conversations")

    assert response.status_code == 201
    assert response.json()["id"]
    assert response.json()["created_at"]


def test_get_conversation_api():
    created = client.post("/conversations").json()

    response = client.get(
        f"/conversations/{created['id']}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]
    assert response.json()["messages"] == []


def test_get_conversation_with_messages():
    created = client.post("/conversations").json()

    add_message(
        created["id"],
        "user",
        "What is RAG?",
        mode="ask",
    )

    response = client.get(
        f"/conversations/{created['id']}"
    )

    assert response.status_code == 200
    assert len(response.json()["messages"]) == 1
    assert response.json()["messages"][0]["content"] == "What is RAG?"


def test_get_unknown_conversation_api():
    response = client.get("/conversations/unknown-id")

    assert response.status_code == 404


def test_list_conversations_empty():
    response = client.get("/conversations")

    assert response.status_code == 200
    assert response.json() == []


def test_list_conversations():
    first = client.post("/conversations").json()
    second = client.post("/conversations").json()

    response = client.get("/conversations")

    assert response.status_code == 200

    conversations = response.json()

    assert len(conversations) == 2
    assert conversations[0]["id"] == second["id"]
    assert conversations[1]["id"] == first["id"]
