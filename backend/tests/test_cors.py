from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)


def test_allowed_cors_origin():
    # Verify an allowed frontend origin
    origin = settings.CORS_ORIGINS[0]

    response = client.options(
        "/chat",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin


def test_disallowed_cors_origin():
    # Reject an unknown browser origin
    response = client.options(
        "/chat",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers