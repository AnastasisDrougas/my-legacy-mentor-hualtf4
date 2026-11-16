
import sys
from pathlib import Path

import pytest

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from context_reasoning import ContextReasoning
from decision_selector import DecisionPatternSelector
from rag_pipeline import RAGPipeline


def test_context_prompt_contains_preconditions():
    patterns = [{
        "principle": "measure before migrating",
        "decisions": [{
            "source_id": "ADR-001",
            "context": "Full table scan",
            "decision": "Add composite index",
            "reasoning": "Reduce unnecessary reads",
            "trade_offs": ["Higher write cost"],
        }],
    }]

    result = ContextReasoning.build_prompt(
        "Indexes work, but writes are blocked.",
        patterns,
    )

    assert "Full table scan" in result
    assert "Indexes work" in result
    assert "Higher write cost" in result
    assert "PARTIALLY MATCHES" in result
    assert "Never blindly repeat" in result


def test_no_historical_precedent():
    result = ContextReasoning.build_prompt(
        "New technical question",
        [],
    )

    assert "No directly retrieved" in result
    assert "Do not invent a precedent" in result


def test_empty_question_rejected():
    with pytest.raises(ValueError):
        ContextReasoning.build_prompt("  ", [])


class FakeRetriever:
    def search(self, question, top_k=5):
        return [{
            "text": "Historical query-plan problem",
            "metadata": {
                "source_id": "ADR-001",
                "title": "Database decision",
                "type": "architecture_decision",
            },
        }]


class SpyLLM:
    def __init__(self):
        self.prompts = []

    def generate(self, system_prompt, user_prompt):
        self.prompts.append(user_prompt)
        return "Test answer"


def test_context_layer_only_used_by_twin():
    llm = SpyLLM()

    pipeline = RAGPipeline(
        retriever=FakeRetriever(),
        llm=llm,
        decision_selector=DecisionPatternSelector(),
    )

    question = (
        "The query plan is already efficient, "
        "but write contention is increasing."
    )

    pipeline.ask(question, mode="baseline")
    pipeline.ask(question, mode="ask")

    baseline, twin = llm.prompts

    assert "CONTEXT-AWARE DECISION ANALYSIS" not in baseline
    assert "CONTEXT-AWARE DECISION ANALYSIS" in twin
    assert "HISTORICAL PRECONDITIONS" in twin
    assert "CURRENT CONDITIONS" in twin
