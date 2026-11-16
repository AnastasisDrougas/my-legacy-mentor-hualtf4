
import sys
from pathlib import Path

import pytest

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from retrieval import SeniorRetriever


def test_database_retrieval():
    retriever = SeniorRetriever()

    results = retriever.search(
        "Why did Alex avoid an immediate database migration "
        "and optimize SQL queries instead?",
        top_k=5,
    )

    assert len(results) == 5

    source_ids = {
        result["metadata"]["source_id"]
        for result in results
    }

    expected = {"ADR-001", "INC-001", "DOC-001"}

    assert source_ids & expected, (
        f"No expected database source retrieved: {source_ids}"
    )


def test_empty_question():
    retriever = SeniorRetriever()

    with pytest.raises(ValueError):
        retriever.search("   ")
