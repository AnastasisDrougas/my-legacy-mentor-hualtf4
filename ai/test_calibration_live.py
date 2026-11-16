
from rag_pipeline import RAGPipeline
from citation_audit import CitationAuditor

question = (
    "Our SQLite queries already use efficient indexes, "
    "but concurrent writes cause frequent database locks. "
    "Would Alex keep adding indexes, or consider another "
    "approach? Explain how his previous decision applies "
    "or differs from this situation."
)

pipeline = RAGPipeline()

result = pipeline.ask(
    question,
    top_k=5,
    mode="ask",
)

print("\nDIGITAL TWIN ANSWER\n")
print(result["answer"])

audit = CitationAuditor.audit(
    result["answer"],
    result["sources"],
)

print("\nCITATION AUDIT")
print("Passed:", audit["passed"])
print("Cited IDs:", audit["cited_ids"])
print("Unsupported IDs:", audit["unsupported_ids"])

print("\nRETRIEVED SOURCES")
for source in result["sources"]:
    print(source["source_id"])
