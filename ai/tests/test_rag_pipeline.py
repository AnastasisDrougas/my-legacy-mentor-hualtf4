
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from rag_pipeline import RAGPipeline


class FakeRetriever:
    def search(self, question, top_k=5):
        assert question
        return [
            {
                "text": "Alex measured slow SQL queries "
                        "and chose indexing before migration.",
                "metadata": {
                    "source_id": "ADR-001",
                    "title": "Order lookup latency",
                    "type": "architecture_decision",
                },
            },
            {
                "text": "Another chunk from the same ADR.",
                "metadata": {
                    "source_id": "ADR-001",
                    "title": "Order lookup latency",
                    "type": "architecture_decision",
                },
            },
        ]


class FakeLLM:
    def generate(self, system_prompt, user_prompt):
        assert "ADR-001" in user_prompt
        assert "SQL queries" in user_prompt
        return "Alex chose indexing after measurement [ADR-001]."


def test_rag_answer_and_source_deduplication():
    pipeline = RAGPipeline(
        retriever=FakeRetriever(),
        llm=FakeLLM(),
    )

    result = pipeline.ask(
        "Why did Alex avoid migration?"
    )

    assert "[ADR-001]" in result["answer"]
    assert len(result["sources"]) == 1
    assert result["sources"][0]["source_id"] == "ADR-001"


def test_empty_question():
    pipeline = RAGPipeline(
        retriever=FakeRetriever(),
        llm=FakeLLM(),
    )

    try:
        pipeline.ask("   ")
        assert False, "Expected ValueError"
    except ValueError:
        pass
