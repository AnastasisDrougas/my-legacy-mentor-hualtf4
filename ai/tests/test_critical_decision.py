
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from ai.critical_decision import CriticalDecisionGuard
from ai.rag_pipeline import RAGPipeline


def test_payment_race_detection():
    categories = CriticalDecisionGuard.detect(
        "Two concurrent payment requests may "
        "cause duplicate charges."
    )

    assert "payment_idempotency" in categories


def test_payment_guardrails():
    prompt = CriticalDecisionGuard.build_prompt(
        "How do we prevent duplicate payment charges?"
    )

    assert "UNIQUE constraint alone" in prompt
    assert "provider-side idempotency" in prompt
    assert "reconciliation" in prompt


def test_security_detection():
    prompt = CriticalDecisionGuard.build_prompt(
        "A cross-tenant vulnerability exposes orders."
    )

    assert "ACTIVE DATA EXPOSURE SAFETY" in prompt
    assert "Stop unauthorized access" in prompt


def test_normal_question_has_no_extra_rules():
    assert CriticalDecisionGuard.build_prompt(
        "How does Python list slicing work?"
    ) == ""


class FakeRetriever:
    def search(self, question, top_k=5):
        return [{
            "text": "Use durable idempotency keys",
            "metadata": {
                "source_id": "ADR-002",
                "title": "Payment retries",
                "type": "architecture_decision",
            },
        }]


class SpyLLM:
    def __init__(self):
        self.prompts = []

    def generate(self, system_prompt, user_prompt):
        self.prompts.append(user_prompt)
        return "Test answer"


def test_guardrails_only_in_twin():
    llm = SpyLLM()

    pipeline = RAGPipeline(
        retriever=FakeRetriever(),
        llm=llm,
    )

    question = (
        "Two concurrent payment requests "
        "may create duplicate charges."
    )

    pipeline.ask(question, mode="baseline")
    pipeline.ask(question, mode="ask")

    baseline, twin = llm.prompts

    assert "CRITICAL ENGINEERING" not in baseline
    assert "CRITICAL ENGINEERING" in twin
    assert "provider-side idempotency" in twin
