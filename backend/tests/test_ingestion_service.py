
import sys
from types import ModuleType

import pytest

from app import database
from app.repositories.documents import (
    create_document,
    get_document,
)
from app.services.ingestion_service import process_document


@pytest.fixture
def document(tmp_path, monkeypatch):
    monkeypatch.setattr(
        database,
        "get_database_path",
        lambda: tmp_path / "ingestion.db",
    )

    database.init_db()

    path = tmp_path / "notes.txt"
    path.write_text("Senior knowledge", encoding="utf-8")

    return create_document(
        filename="notes.txt",
        storage_path=str(path),
        content_type="text/plain",
        size_bytes=path.stat().st_size,
    )


def test_successful_ingestion(document, monkeypatch):
    module = ModuleType("ai.ingestion")
    module.ingest_document = lambda path: {
        "chunks_added": 1,
    }

    monkeypatch.setitem(sys.modules, "ai.ingestion", module)

    process_document(document["id"])

    saved = get_document(document["id"])
    assert saved["status"] == "ready"
    assert saved["error_message"] is None


def test_failed_ingestion(document, monkeypatch):
    def fail(path):
        raise RuntimeError("Simulated ingestion failure")

    module = ModuleType("ai.ingestion")
    module.ingest_document = fail

    monkeypatch.setitem(sys.modules, "ai.ingestion", module)

    process_document(document["id"])

    saved = get_document(document["id"])
    assert saved["status"] == "failed"
    assert saved["error_message"] == "Document ingestion failed"


def test_unknown_document():
    with pytest.raises(ValueError):
        process_document("unknown-id")


def test_ingestion_passes_original_filename(document, monkeypatch):
    captured = {}

    def fake_ingest(path, title=None):
        captured["path"] = path
        captured["title"] = title
        return {"chunks_added": 1}

    module = ModuleType("ai.ingestion")
    module.ingest_document = fake_ingest

    monkeypatch.setitem(sys.modules, "ai.ingestion", module)

    process_document(document["id"])

    assert captured["path"] == document["storage_path"]
    assert captured["title"] == "notes.txt"
    assert get_document(document["id"])["status"] == "ready"
