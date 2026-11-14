from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_unknown_endpoint():
    # Unknown endpoints should return 404
    response = client.get("/unknown")

    assert response.status_code == 404


def test_chat_wrong_method():
    # Chat only accepts POST requests
    response = client.get("/chat")

    assert response.status_code == 405