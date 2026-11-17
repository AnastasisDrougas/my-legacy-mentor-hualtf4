
from rag_pipeline import RAGPipeline

question = (
    "Should we immediately migrate the Orders API "
    "from SQLite to PostgreSQL because queries are slow?"
)

pipeline = RAGPipeline()

for mode in ("baseline", "ask", "mentor"):
    print("\n" + "=" * 60)
    print(f"MODE: {mode.upper()}")
    print("=" * 60)

    result = pipeline.ask(question, mode=mode)

    print(result["answer"])

    print("\nSOURCES:")
    for source in result["sources"]:
        print("-", source["source_id"])
