
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from multi_topic_retrieval import (
    MultiTopicRetriever,
    detect_topics,
    source_identity,
)


def item(source_id):
    return {
        "text": f"Evidence from {source_id}",
        "metadata": {
            "source_id": source_id,
            "title": source_id,
            "type": "architecture_decision",
        },
    }


class FakeRetriever:
    def __init__(self):
        self.calls = []

    def search(self, question, top_k=5):
        self.calls.append((question, top_k))
        q = question.casefold()

        if "write lock contention" in q:
            return [item("ADR-001"), item("DOC-001")]

        if "unknown outcome" in q:
            return [item("INC-002"), item("DOC-010")]

        if "performance guardrails" in q:
            return [item("ADR-012"), item("DOC-012")]

        return [
            item("PR-009"),
            item("DOC-010"),
            item("INC-009"),
        ][:top_k]


def test_detect_three_topics():
    question = (
        "SQLite locks, payment timeouts "
        "and a release today."
    )

    assert detect_topics(question) == [
        "database",
        "payments",
        "deployment",
    ]


def test_single_topic_uses_original_search():
    fake = FakeRetriever()
    retriever = MultiTopicRetriever(fake)

    result = retriever.search(
        "Why is SQLite locked?",
        top_k=3,
    )

    assert len(fake.calls) == 1
    assert result[0]["metadata"]["source_id"] == "PR-009"


def test_multi_topic_evidence_coverage():
    fake = FakeRetriever()
    retriever = MultiTopicRetriever(fake)

    results = retriever.search(
        "SQLite locks, payment timeout, deployment risk",
        top_k=5,
    )

    ids = {
        source_identity(value)
        for value in results
    }

    assert "ADR-001" in ids
    assert "INC-002" in ids
    assert "ADR-012" in ids
    assert len(results) <= 5


def test_deduplication():
    fake = FakeRetriever()
    retriever = MultiTopicRetriever(fake)

    results = retriever.search(
        "SQLite locks, payment retries, release today",
        top_k=5,
    )

    ids = [source_identity(x) for x in results]

    assert len(ids) == len(set(ids))


def test_top_k_respected():
    retriever = MultiTopicRetriever(FakeRetriever())

    results = retriever.search(
        "SQLite locks and payment retries",
        top_k=2,
    )

    assert len(results) <= 2


def test_empty_topic_detection():
    assert detect_topics(
        "Explain Python list slicing"
    ) == []


def test_invalid_top_k():
    retriever = MultiTopicRetriever(FakeRetriever())

    try:
        retriever.search("SQLite and payment", top_k=0)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")
