from fastapi.testclient import TestClient
import pytest
from app import database
from app.main import app
from app.services import ai_service

client = TestClient(app)
@pytest.fixture(autouse=True)
def temporary_database(tmp_path, monkeypatch):
    # Initialize a separate database for each test
    monkeypatch.setattr(
        database,
        "get_database_path",
        lambda: tmp_path / "ai_integration_test.db",
    )
    database.init_db()


class FakePipeline:
    def ask(self, question, top_k=5, mode="ask"):
        # Simulate the RAG response without an API key
        return {
            "answer": f"AI answer for: {question}",
            "sources": [
                {
                    "source_id": "ADR-001",
                    "title": "Database Optimization",
                    "type": "architecture_decision",
                }
            ],
        }


def test_ai_integration_ask(monkeypatch):
    monkeypatch.setattr(ai_service, "get_pipeline", lambda: FakePipeline())

    response = client.post("/chat", json={
        "question": "Why optimize SQL queries?",
        "mode": "ask",
    })

    assert response.status_code == 200
    assert response.json()["answer"] == "AI answer for: Why optimize SQL queries?"
    assert response.json()["sources"][0]["source_id"] == "ADR-001"


def test_ai_integration_mentor(monkeypatch):
    monkeypatch.setattr(ai_service, "get_pipeline", lambda: FakePipeline())

    response = client.post("/chat", json={
        "question": "How should I improve?",
        "mode": "mentor",
    })

    assert response.status_code == 200
    assert response.json()["mode"] == "mentor"