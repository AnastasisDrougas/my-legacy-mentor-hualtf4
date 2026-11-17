import pytest
from fastapi.testclient import TestClient
from app import database
from app.main import app
from app.services import ai_service

client = TestClient(app)


class FakePipeline:
    def ask(self, question, top_k=5, mode="ask"):
        return {
            "answer": f"Question: {question}",
            "sources": [
                {
                    "source_id": "ADR-001",
                    "title": "Database Optimization",
                    "type": "architecture_decision",
                }
            ],
        }


@pytest.fixture(autouse=True)
def mock_pipeline(monkeypatch, tmp_path):
    # Isolate SQLite for each test
    monkeypatch.setattr(
        database,
        "get_database_path",
        lambda: tmp_path / "chat_test.db",
    )
    database.init_db()

    # Avoid external LLM calls
    monkeypatch.setattr(
        ai_service,
        "get_pipeline",
        lambda: FakePipeline(),
    )


def test_chat_ask():
    response = client.post(
        "/chat",
        json={"question": "What is RAG?", "mode": "ask"},
    )

    assert response.status_code == 200
    assert response.json()["mode"] == "ask"


def test_chat_mentor():
    response = client.post(
        "/chat",
        json={"question": "How can I improve?", "mode": "mentor"},
    )

    assert response.status_code == 200
    assert response.json()["mode"] == "mentor"


def test_chat_default_mode():
    response = client.post(
        "/chat",
        json={"question": "What is RAG?"},
    )

    assert response.status_code == 200
    assert response.json()["mode"] == "ask"


def test_chat_trim_question():
    response = client.post(
        "/chat",
        json={"question": "   What is RAG?   ", "mode": "ask"},
    )

    assert response.status_code == 200
    assert response.json()["answer"] == "Question: What is RAG?"


def test_chat_empty_question():
    response = client.post("/chat", json={"question": ""})

    assert response.status_code == 422


def test_chat_whitespace_question():
    response = client.post("/chat", json={"question": "   "})

    assert response.status_code == 422


def test_chat_invalid_mode():
    response = client.post(
        "/chat",
        json={"question": "Hello", "mode": "invalid"},
    )

    assert response.status_code == 422


def test_chat_missing_question():
    response = client.post("/chat", json={"mode": "ask"})

    assert response.status_code == 422


def test_chat_sources():
    response = client.post(
        "/chat",
        json={"question": "Explain database optimization"},
    )

    assert response.status_code == 200
    assert response.json()["sources"] == [
        {
            "source_id": "ADR-001",
            "title": "Database Optimization",
            "type": "architecture_decision",
        }
    ]