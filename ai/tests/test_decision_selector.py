
import sys
from pathlib import Path

import pytest

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from ai.decision_selector import DecisionPatternSelector
from ai.rag_pipeline import RAGPipeline


class FakeRetriever:
    def search(self, question, top_k=5):
        return [
            {
                "text": "Alex chose an index before migration.",
                "metadata": {
                    "source_id": "ADR-001",
                    "title": "Database decision",
                    "type": "architecture_decision",
                },
            },
            {
                "text": "The team tested the query plan.",
                "metadata": {
                    "source_id": "INC-001",
                    "title": "Slow database query",
                    "type": "incident",
                },
            },
        ]


class SpyLLM:
    def __init__(self):
        self.calls = []

    def generate(self, system_prompt, user_prompt):
        self.calls.append({
            "system": system_prompt,
            "user": user_prompt,
        })
        return "Measured optimization first [ADR-001]."


def test_selects_relevant_pattern():
    selector = DecisionPatternSelector()

    patterns = selector.select(
        FakeRetriever().search("database")
    )

    ids = {p["pattern_id"] for p in patterns}

    assert "measure_before_migrating" in ids


def test_unknown_sources_return_no_patterns():
    selector = DecisionPatternSelector()

    patterns = selector.select([{
        "metadata": {"source_id": "UNKNOWN-999"}
    }])

    assert patterns == []


def test_invalid_top_k():
    selector = DecisionPatternSelector()

    with pytest.raises(ValueError):
        selector.select([], top_k=0)


def test_twin_receives_patterns_baseline_does_not():
    llm = SpyLLM()

    pipeline = RAGPipeline(
        retriever=FakeRetriever(),
        llm=llm,
    )

    pipeline.ask("Should we migrate?", mode="baseline")
    pipeline.ask("Should we migrate?", mode="ask")
    pipeline.ask("Should we migrate?", mode="mentor")

    baseline = llm.calls[0]["user"]
    ask = llm.calls[1]["user"]
    mentor = llm.calls[2]["user"]

    assert "EVIDENCE-BACKED DECISION PATTERNS" not in baseline

    assert "measure_before_migrating" in ask
    assert "measure_before_migrating" in mentor

    assert "ADR-001" in baseline
    assert "ADR-001" in ask
    assert "ADR-001" in mentor


def test_pattern_source_traceability():
    selector = DecisionPatternSelector()

    sources = FakeRetriever().search("database")
    selected = selector.select(sources)

    retrieved_ids = {
        x["metadata"]["source_id"] for x in sources
    }

    for pattern in selected:
        assert set(
            pattern["matched_evidence_ids"]
        ).issubset(retrieved_ids)
