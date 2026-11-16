
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from citation_audit import CitationAuditor
from ai.decision_calibration import DecisionCalibration
from ai.rag_pipeline import RAGPipeline


def test_calibration_rules_present():
    prompt = DecisionCalibration.build_prompt()

    assert "SEPARATE FACTS FROM INFERENCE" in prompt
    assert "CHECK TECHNOLOGY COMPATIBILITY" in prompt
    assert "CALIBRATE CONFIDENCE" in prompt
    assert "HISTORICAL PRECEDENT" in prompt


def test_valid_citations_pass():
    result = CitationAuditor.audit(
        "Alex chose indexing [ADR-001].",
        [{"source_id": "ADR-001"}],
    )

    assert result["passed"] is True
    assert result["unsupported_ids"] == []


def test_fabricated_citation_detected():
    result = CitationAuditor.audit(
        "See [ADR-001] and [ADR-999].",
        [{"source_id": "ADR-001"}],
    )

    assert result["passed"] is False
    assert result["unsupported_ids"] == ["ADR-999"]


def test_uncited_retrieved_source_not_fabricated():
    result = CitationAuditor.audit(
        "The index needs measurement [ADR-001].",
        [
            {"source_id": "ADR-001"},
            {"source_id": "PR-002"},
        ],
    )

    assert result["passed"] is True
    assert result["cited_ids"] == ["ADR-001"]


class FakeRetriever:
    def search(self, question, top_k=5):
        return [{
            "text": "Historical read latency was addressed with an index.",
            "metadata": {
                "source_id": "ADR-001",
                "title": "Order lookup latency",
                "type": "architecture_decision",
            },
        }]


class SpyLLM:
    def __init__(self):
        self.prompts = []

    def generate(self, system_prompt, user_prompt):
        self.prompts.append(user_prompt)
        return "Test response [ADR-001]."


def test_calibration_only_applies_to_twin():
    llm = SpyLLM()

    pipeline = RAGPipeline(
        retriever=FakeRetriever(),
        llm=llm,
    )

    pipeline.ask("Why was indexing chosen?", mode="baseline")
    pipeline.ask("Why was indexing chosen?", mode="ask")
    pipeline.ask("Why was indexing chosen?", mode="mentor")

    baseline, ask, mentor = llm.prompts

    assert "DECISION CALIBRATION RULES" not in baseline
    assert "DECISION CALIBRATION RULES" in ask
    assert "DECISION CALIBRATION RULES" in mentor
