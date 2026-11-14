from fastapi.testclient import TestClient
from app.main import app

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