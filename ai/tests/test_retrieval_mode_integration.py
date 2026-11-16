
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from ai.rag_pipeline import RAGPipeline
from ai.multi_topic_retrieval import MultiTopicRetriever


def evidence(source_id):
    return {
        "text": f"Historical evidence: {source_id}",
        "metadata": {
            "source_id": source_id,
            "title": f"Document {source_id}",
            "type": "technical_document",
        },
    }


class FakeRetriever:
    def __init__(self):
        self.calls = []

    def search(self, question, top_k=5):
        self.calls.append((question, top_k))
        q = question.casefold()

        if "write lock contention" in q:
            return [evidence("ADR-001")]

        if "unknown outcome" in q:
            return [evidence("INC-002")]

        if "performance guardrails" in q:
            return [evidence("ADR-012")]

        return [evidence("DOC-009")]


class FakeLLM:
    def generate(self, system_prompt, user_prompt):
        return "Grounded test response [DOC-009]"


class FakePersona:
    def build_system_prompt(self, mode):
        return f"Test prompt for {mode}"


class FakeDecisionSelector:
    def select(self, sources, top_k=3):
        return []

    def format_for_prompt(self, selected_patterns):
        return ""


def make_pipeline(retriever):
    return RAGPipeline(
        retriever=retriever,
        llm=FakeLLM(),
        persona=FakePersona(),
        decision_selector=FakeDecisionSelector(),
    )


QUESTION = (
    "SQLite write locks, payment provider "
    "unknown outcomes and deployment release risk."
)


def test_baseline_keeps_original_retrieval():
    fake = FakeRetriever()
    pipeline = make_pipeline(fake)

    result = pipeline.ask(
        QUESTION,
        mode="baseline",
    )

    assert len(fake.calls) == 1
    assert result["sources"][0]["source_id"] == "INC-002"


def test_ask_uses_multi_topic_retrieval():
    fake = FakeRetriever()
    pipeline = make_pipeline(fake)

    result = pipeline.ask(
        QUESTION,
        mode="ask",
    )

    ids = {
        x["source_id"]
        for x in result["sources"]
    }

    assert len(fake.calls) == 4
    assert {"ADR-001", "INC-002", "ADR-012"} <= ids


def test_mentor_uses_multi_topic_retrieval():
    fake = FakeRetriever()
    pipeline = make_pipeline(fake)

    result = pipeline.ask(
        QUESTION,
        mode="mentor",
    )

    ids = {
        x["source_id"]
        for x in result["sources"]
    }

    assert {"ADR-001", "INC-002", "ADR-012"} <= ids


def test_single_topic_stays_single_search():
    fake = FakeRetriever()
    pipeline = make_pipeline(fake)

    pipeline.ask(
        "Explain SQLite indexes",
        mode="ask",
    )

    assert len(fake.calls) == 1


def test_baseline_unwraps_injected_multi_retriever():
    fake = FakeRetriever()
    wrapped = MultiTopicRetriever(fake)
    pipeline = make_pipeline(wrapped)

    pipeline.ask(
        QUESTION,
        mode="baseline",
    )

    assert len(fake.calls) == 1


def test_response_contract_is_preserved():
    pipeline = make_pipeline(FakeRetriever())

    result = pipeline.ask(
        QUESTION,
        mode="ask",
        top_k=3,
    )

    assert set(result) == {"answer", "sources"}
    assert len(result["sources"]) <= 3

    for source in result["sources"]:
        assert set(source) == {
            "source_id",
            "title",
            "type",
        }
