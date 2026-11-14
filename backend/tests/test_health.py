from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    # Check the health endpoint
    response = client.get("/health")

    assert response.status_code == 200

    # Verify the response data
    assert response.json() == {
        "status": "ok",
        "service": "knowledge-legacy-backend"
    }