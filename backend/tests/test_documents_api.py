
import pytest
from fastapi.testclient import TestClient

from app import database
from app.main import app
from app.services import document_service


client = TestClient(app)


@pytest.fixture(autouse=True)
def temporary_storage(tmp_path, monkeypatch):
    # Isolate document uploads from local data
    monkeypatch.setattr(
        database,
        "get_database_path",
        lambda: tmp_path / "api_test.db",
    )
    monkeypatch.setattr(
        document_service,
        "get_upload_directory",
        lambda: tmp_path / "uploads",
    )
    database.init_db()


def test_upload_document():
    response = client.post(
        "/documents",
        files={
            "file": ("notes.txt", b"Senior knowledge", "text/plain")
        },
    )

    assert response.status_code == 201
    assert response.json()["filename"] == "notes.txt"
    assert response.json()["status"] == "uploaded"
    assert "storage_path" not in response.json()


def test_get_uploaded_document():
    created = client.post(
        "/documents",
        files={
            "file": ("guide.md", b"# Guide", "text/markdown")
        },
    ).json()

    response = client.get(f"/documents/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]
    assert response.json()["status"] == "uploaded"


def test_reject_invalid_extension():
    response = client.post(
        "/documents",
        files={
            "file": (
                "script.exe",
                b"invalid",
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 400


def test_reject_empty_document():
    response = client.post(
        "/documents",
        files={
            "file": ("empty.txt", b"", "text/plain")
        },
    )

    assert response.status_code == 400


def test_get_unknown_document():
    response = client.get("/documents/unknown-id")

    assert response.status_code == 404


def test_upload_missing_file():
    response = client.post("/documents")

    assert response.status_code == 422
