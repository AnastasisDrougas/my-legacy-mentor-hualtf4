
import pytest

from app import database
from app.repositories.documents import (
    create_document,
    get_document,
    update_document_status,
)


@pytest.fixture(autouse=True)
def temporary_database(tmp_path, monkeypatch):
    # Use an isolated SQLite database
    monkeypatch.setattr(
        database,
        "get_database_path",
        lambda: tmp_path / "documents_test.db",
    )
    database.init_db()


def test_create_document():
    document = create_document(
        "architecture.pdf",
        "uploads/test.pdf",
        "application/pdf",
        2048,
    )

    assert document["id"]
    assert document["filename"] == "architecture.pdf"
    assert document["status"] == "uploaded"
    assert document["size_bytes"] == 2048


def test_get_document():
    document = create_document(
        "notes.txt",
        "uploads/notes.txt",
        "text/plain",
        100,
    )

    result = get_document(document["id"])

    assert result["id"] == document["id"]


def test_unknown_document():
    assert get_document("unknown-id") is None


def test_update_document_status():
    document = create_document(
        "incident.txt",
        "uploads/incident.txt",
        "text/plain",
        500,
    )

    updated = update_document_status(
        document["id"],
        "processing",
    )

    assert updated is True
    assert get_document(document["id"])["status"] == "processing"


def test_invalid_document_status():
    document = create_document(
        "test.txt",
        "uploads/test.txt",
        "text/plain",
        100,
    )

    with pytest.raises(ValueError):
        update_document_status(
            document["id"],
            "invalid",
        )


def test_negative_document_size():
    with pytest.raises(ValueError):
        create_document(
            "test.txt",
            "uploads/test.txt",
            "text/plain",
            -1,
        )
