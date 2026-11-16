
import json
from pathlib import Path

from rag_pipeline import RAGPipeline
from retrieval import SeniorRetriever
from multi_topic_retrieval import MultiTopicRetriever
question = """
You are Alex Morgan, the senior engineer.

We are preparing a checkout release today.

Three problems appeared simultaneously:

1. SQLite write transactions sometimes remain open
   for three seconds and produce database lock errors.

2. The payment provider occasionally times out.
   Some requests have an unknown payment outcome.

3. Management wants the release deployed today
   because an important customer is waiting.

A junior developer proposes:
- Adding a composite database index.
- Retrying all payment requests automatically.
- Deploying the full release immediately.

What would you decide?

Explain:
1. Your immediate go/no-go decision.
2. Which proposed fixes are unsafe or insufficient.
3. What evidence you need.
4. The safest technical actions, in priority order.
5. How your previous engineering decisions apply
   or differ from this situation.
6. Your confidence and missing information.

Cite real historical source IDs.
Do not invent production metrics or guarantees.
"""

pipeline = RAGPipeline()

result = pipeline.ask(
    question,
    top_k=5,
    mode="ask",
)

print("\n" + "=" * 60)
print("SENIOR DIGITAL TWIN — CHALLENGE")
print("=" * 60)
print(result["answer"])

print("\nRETRIEVED SOURCES")
for source in result["sources"]:
    print(source["source_id"], "-", source["title"])

output = Path("ai/evaluation/results/senior_challenge.json")
output.parent.mkdir(parents=True, exist_ok=True)

output.write_text(
    json.dumps(
        {
            "question": question,
            "answer": result["answer"],
            "sources": result["sources"],
        },
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)

print("\nSaved:", output)
