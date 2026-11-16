
from rag_pipeline import RAGPipeline

question = (
    "A service is experiencing high latency. "
    "Its database indexes and query plans are efficient, "
    "but many concurrent writes cause lock contention. "
    "Should we add another index or investigate a "
    "different storage architecture? "
    "Explain which historical engineering principles "
    "still apply and which past implementation choices "
    "may no longer be appropriate."
)

pipeline = RAGPipeline()

result = pipeline.ask(
    question,
    top_k=5,
    mode="ask",
)

print("\nDIGITAL TWIN ANSWER\n")
print(result["answer"])

print("\nSOURCES\n")
for source in result["sources"]:
    print(source["source_id"])
