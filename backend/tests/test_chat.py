from fastapi.testclient import TestClient
from app.main import app
from app.services import ai_service


client = TestClient(app)


def test_chat_ask():
    # Test chat in Ask mode
    response = client.post("/chat", json={
        "question": "How do we handle incidents?",
        "mode": "ask"
    })

    assert response.status_code == 200
    assert response.json()["mode"] == "ask"
    assert response.json()["sources"] == []


def test_chat_mentor():
    # Test chat in Mentor mode
    response = client.post("/chat", json={
        "question": "How can I improve my code?",
        "mode": "mentor"
    })

    assert response.status_code == 200
    assert response.json()["mode"] == "mentor"


def test_chat_invalid_mode():
    # Reject unsupported chat modes
    response = client.post("/chat", json={
        "question": "Hello",
        "mode": "invalid"
    })

    assert response.status_code == 422


def test_chat_empty_question():
    # Reject empty questions
    response = client.post("/chat", json={
        "question": "",
        "mode": "ask"
    })

    assert response.status_code == 422

def test_chat_whitespace_question():
    # Reject whitespace-only questions
    response = client.post("/chat", json={
        "question": "   ",
        "mode": "ask"
    })

    assert response.status_code == 422


def test_chat_trim_question():
    # Remove unnecessary spaces
    response = client.post("/chat", json={
        "question": "   What is RAG?   ",
        "mode": "ask"
    })

    assert response.status_code == 200
    assert response.json()["answer"] == "Mock response to: What is RAG?"


def test_chat_missing_question():
    # Reject requests without a question
    response = client.post("/chat", json={
        "mode": "ask"
    })

    assert response.status_code == 422


def test_chat_ai_failure(monkeypatch):
    # Simulate an AI service failure
    def failing_answer(request):
        raise ai_service.AIServiceError("Provider unavailable")

    monkeypatch.setattr(ai_service, "generate_answer", failing_answer)

    response = client.post("/chat", json={
        "question": "How should I debug this?",
        "mode": "mentor"
    })

    assert response.status_code == 503
    assert response.json() == {
        "detail": "AI service is temporarily unavailable"
    }


def test_chat_default_mode():
    # Verify the default Ask mode
    response = client.post("/chat", json={
        "question": "What is RAG?"
    })

    assert response.status_code == 200
    assert response.json()["mode"] == "ask"

def test_chat_missing_mode_defaults_to_ask():
    # Check default mode
    response = client.post("/chat", json={
        "question": "Explain dependency injection"
    })

    assert response.status_code == 200
    assert response.json()["mode"] == "ask"


def test_chat_wrong_question_type():
    # Reject non-string questions
    response = client.post("/chat", json={
        "question": 123,
        "mode": "ask"
    })

    assert response.status_code == 422