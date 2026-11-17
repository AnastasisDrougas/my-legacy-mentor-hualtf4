
from rag_pipeline import RAGPipeline
from citation_audit import CitationAuditor

question = (
    "Two concurrent payment requests use the same "
    "idempotency key. One worker may crash after "
    "calling the payment provider but before saving "
    "the result. Explain how to prevent duplicate "
    "charges, handle the uncertain outcome, and "
    "verify the solution with concurrency tests."
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
print("Unsupported:", audit["unsupported_ids"])
