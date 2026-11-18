
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import pytest

from app import database
from app.services import document_service


@pytest.fixture(autouse=True)
def temporary_storage(tmp_path, monkeypatch):
    # Isolate database and uploaded files
    monkeypatch.setattr(
        database,
        "get_database_path",
        lambda: tmp_path / "documents.db",
    )
    monkeypatch.setattr(
        document_service,
        "get_upload_directory",
        lambda: tmp_path / "uploads",
    )
    database.init_db()


def make_file(filename, content_type, content):
    return SimpleNamespace(
        filename=filename,
        content_type=content_type,
        file=BytesIO(content),
    )


def test_store_txt_document(tmp_path):
    document = document_service.store_document(
        make_file("notes.txt", "text/plain", b"Senior notes")
    )

    assert document["status"] == "uploaded"
    assert document["size_bytes"] == 12
    assert Path(document["storage_path"]).read_bytes() == b"Senior notes"


def test_store_markdown_document():
    document = document_service.store_document(
        make_file("guide.md", "text/markdown", b"# Guide")
    )

    assert document["filename"] == "guide.md"
    assert document["content_type"] == "text/markdown"


def test_store_pdf_document():
    document = document_service.store_document(
        make_file("architecture.pdf", "application/pdf", b"%PDF-1.4\nTest")
    )

    assert document["status"] == "uploaded"


def test_reject_unsupported_file():
    with pytest.raises(document_service.DocumentValidationError):
        document_service.store_document(
            make_file("script.exe", "application/octet-stream", b"test")
        )


def test_reject_invalid_content_type():
    with pytest.raises(document_service.DocumentValidationError):
        document_service.store_document(
            make_file("notes.txt", "application/pdf", b"test")
        )


def test_reject_empty_file():
    with pytest.raises(document_service.DocumentValidationError):
        document_service.store_document(
            make_file("empty.txt", "text/plain", b"")
        )


def test_reject_invalid_pdf():
    with pytest.raises(document_service.DocumentValidationError):
        document_service.store_document(
            make_file("fake.pdf", "application/pdf", b"Not a PDF")
        )


def test_reject_oversized_file(monkeypatch):
    monkeypatch.setattr(
        document_service,
        "MAX_FILE_SIZE",
        10,
    )

    with pytest.raises(document_service.DocumentValidationError):
        document_service.store_document(
            make_file("large.txt", "text/plain", b"A" * 11)
        )


def test_rejected_file_is_removed(tmp_path):
    with pytest.raises(document_service.DocumentValidationError):
        document_service.store_document(
            make_file("invalid.pdf", "application/pdf", b"invalid")
        )

    upload_dir = tmp_path / "uploads"

    assert list(upload_dir.iterdir()) == []
