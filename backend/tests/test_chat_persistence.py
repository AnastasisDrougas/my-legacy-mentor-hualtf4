
import pytest
from fastapi.testclient import TestClient

from app import database
from app.main import app
from app.services import ai_service

client = TestClient(app)


class FakePipeline:
    def ask(self, question, top_k=5, mode="ask"):
        return {
            "answer": f"Answer to: {question}",
            "sources": [
                {
                    "source_id": "DOC-001",
                    "title": "Engineering Guide",
                    "type": "technical_document",
                }
            ],
        }


@pytest.fixture(autouse=True)
def setup_test_database(tmp_path, monkeypatch):
    # Isolate persistence and mock the external LLM
    monkeypatch.setattr(
        database,
        "get_database_path",
        lambda: tmp_path / "chat_test.db",
    )
    database.init_db()

    monkeypatch.setattr(
        ai_service,
        "get_pipeline",
        lambda: FakePipeline(),
    )


def test_chat_creates_and_saves_conversation():
    response = client.post(
        "/chat",
        json={"question": "What is RAG?", "mode": "ask"},
    )

    assert response.status_code == 200

    conversation_id = response.headers["X-Conversation-ID"]

    history = client.get(
        f"/conversations/{conversation_id}"
    )

    assert history.status_code == 200

    messages = history.json()["messages"]

    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "What is RAG?"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["mode"] == "ask"
    assert messages[1]["sources"][0]["source_id"] == "DOC-001"


def test_chat_reuses_existing_conversation():
    first = client.post(
        "/chat",
        json={"question": "First question"},
    )

    conversation_id = first.headers["X-Conversation-ID"]

    second = client.post(
        "/chat",
        headers={"X-Conversation-ID": conversation_id},
        json={
            "question": "Second question",
            "mode": "mentor",
        },
    )

    assert second.status_code == 200
    assert second.headers["X-Conversation-ID"] == conversation_id

    history = client.get(
        f"/conversations/{conversation_id}"
    )

    messages = history.json()["messages"]

    assert len(messages) == 4
    assert messages[2]["content"] == "Second question"
    assert messages[3]["mode"] == "mentor"


def test_chat_rejects_unknown_conversation():
    response = client.post(
        "/chat",
        headers={"X-Conversation-ID": "unknown-id"},
        json={"question": "Hello"},
    )

    assert response.status_code == 404


def test_failed_ai_does_not_save_messages(monkeypatch):
    # Simulate an AI failure
    class FailingPipeline:
        def ask(self, question, top_k=5, mode="ask"):
            raise RuntimeError("AI unavailable")

    monkeypatch.setattr(
        ai_service,
        "get_pipeline",
        lambda: FailingPipeline(),
    )

    response = client.post(
        "/chat",
        json={"question": "Test failed AI"},
    )

    assert response.status_code == 503

    with database.get_db_connection() as connection:
        conversations = connection.execute(
            "SELECT COUNT(*) FROM conversations"
        ).fetchone()[0]

        messages = connection.execute(
            "SELECT COUNT(*) FROM messages"
        ).fetchone()[0]

    assert conversations == 0
    assert messages == 0
