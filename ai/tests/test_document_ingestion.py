
from pathlib import Path
from unittest.mock import patch

import chromadb
import pytest

import ai.ingestion as ingestion


@pytest.fixture
def isolated_chroma(tmp_path):
    database = tmp_path / "chroma"
    client = chromadb.PersistentClient(path=str(database))
    client.create_collection(
        name=ingestion.COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    with patch.object(ingestion, "CHROMA_PATH", database):
        yield client.get_collection(ingestion.COLLECTION_NAME)


def test_txt_ingestion_and_duplicate(tmp_path, isolated_chroma):
    document = tmp_path / "incident.txt"
    document.write_text(
        "Synthetic incident: Alex optimized SQL indexes.",
        encoding="utf-8",
    )

    first = ingestion.ingest_document(str(document))
    second = ingestion.ingest_document(str(document))

    assert first["chunks_added"] == 1
    assert second["chunks_added"] == 0
    assert isolated_chroma.count() == 1


@pytest.mark.parametrize(
    "filename,content,error",
    [
        ("missing.txt", None, FileNotFoundError),
        ("empty.txt", "", ValueError),
        ("invalid.exe", "test", ValueError),
    ],
)
def test_invalid_uploads(tmp_path, filename, content, error):
    path = tmp_path / filename

    if content is not None:
        path.write_text(content, encoding="utf-8")

    with pytest.raises(error):
        ingestion.ingest_document(str(path))
