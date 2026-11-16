
import sys
from pathlib import Path

import pytest

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from persona import PersonaEngine
from rag_pipeline import RAGPipeline


class FakeRetriever:
    def search(self, question, top_k=5):
        return [{
            "text": (
                "Alex inspected query plans and selected "
                "an index before considering migration."
            ),
            "metadata": {
                "source_id": "ADR-001",
                "title": "Order lookup latency",
                "type": "architecture_decision",
            },
        }]


class SpyLLM:
    def __init__(self):
        self.calls = []

    def generate(self, system_prompt, user_prompt):
        self.calls.append({
            "system": system_prompt,
            "user": user_prompt,
        })
        return "The decision was evidence-driven [ADR-001]."


def test_persona_loads():
    persona = PersonaEngine()

    assert persona.senior_id == "senior_001"
    assert persona.name == "Alex Morgan"


def test_ask_mode():
    prompt = PersonaEngine().build_system_prompt("ask")

    assert "MODE: ASK" in prompt
    assert "Alex Morgan" in prompt


def test_mentor_mode():
    prompt = PersonaEngine().build_system_prompt("mentor")

    assert "MODE: MENTOR" in prompt
    assert "guiding question" in prompt


def test_baseline_has_no_persona():
    prompt = PersonaEngine().build_system_prompt("baseline")

    assert "Alex Morgan" not in prompt
    assert "Do not imitate" in prompt


def test_invalid_mode():
    with pytest.raises(ValueError):
        PersonaEngine().build_system_prompt("invalid")


def test_pipeline_uses_selected_mode():
    llm = SpyLLM()

    pipeline = RAGPipeline(
        retriever=FakeRetriever(),
        llm=llm,
    )

    for mode in ("ask", "mentor", "baseline"):
        result = pipeline.ask(
            "Why avoid PostgreSQL migration?",
            mode=mode,
        )
        assert result["sources"][0]["source_id"] == "ADR-001"

    assert "MODE: ASK" in llm.calls[0]["system"]
    assert "MODE: MENTOR" in llm.calls[1]["system"]
    assert "Do not imitate" in llm.calls[2]["system"]

    # Same question and retrieved source for fair comparison.
    assert all(
        "ADR-001" in call["user"]
        for call in llm.calls
    )
