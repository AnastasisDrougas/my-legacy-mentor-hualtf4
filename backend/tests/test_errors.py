from fastapi.testclient import TestClient

from app.main import app
from app.services import ai_service

client = TestClient(app)


def test_unknown_endpoint():
    response = client.get("/nonexistent")
    assert response.status_code == 404


def test_chat_wrong_method():
    response = client.get("/chat")
    assert response.status_code == 405


def test_chat_ai_failure_returns_503(monkeypatch):
    class FailingPipeline:
        def ask(self, question, top_k=5, mode="ask"):
            raise RuntimeError("Internal AI failure")

    monkeypatch.setattr(
        ai_service,
        "get_pipeline",
        lambda: FailingPipeline(),
    )

    response = client.post(
        "/chat",
        json={
            "question": "Explain RAG",
            "mode": "ask",
        },
    )

    assert response.status_code == 503
    assert "Internal AI failure" not in response.text