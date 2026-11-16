
import chromadb
from sentence_transformers import SentenceTransformer

from ingestion import (
    CHROMA_PATH,
    COLLECTION_NAME,
    MODEL_NAME,
)


class SeniorRetriever:
    def __init__(self):
        self.model = SentenceTransformer(
            MODEL_NAME,
            device="cpu",
        )

        self.client = chromadb.PersistentClient(
            path=str(CHROMA_PATH)
        )

        self.collection = self.client.get_collection(
            COLLECTION_NAME
        )

    def search(self, question: str, top_k: int = 5):
        if not question.strip():
            raise ValueError("Question cannot be empty")

        if top_k < 1:
            raise ValueError("top_k must be positive")

        query_embedding = self.model.encode(
            question,
            normalize_embeddings=True,
        )

        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=min(top_k, self.collection.count()),
            include=[
                "documents",
                "metadatas",
                "distances",
            ],
        )

        matches = []

        for i, chunk_id in enumerate(results["ids"][0]):
            matches.append({
                "chunk_id": chunk_id,
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            })

        return matches


if __name__ == "__main__":
    retriever = SeniorRetriever()

    question = (
        "Why did Alex prefer optimizing SQL queries "
        "instead of immediately migrating to PostgreSQL?"
    )

    print(f"\nQUESTION: {question}\n")

    for rank, result in enumerate(
        retriever.search(question, top_k=5), 1
    ):
        metadata = result["metadata"]

        print(f"RESULT {rank}")
        print("Source:", metadata["source_id"])
        print("Title:", metadata["title"])
        print("Type:", metadata["type"])
        print("Distance:", round(result["distance"], 4))
        print("Text:", result["text"][:250])
        print("-" * 60)
