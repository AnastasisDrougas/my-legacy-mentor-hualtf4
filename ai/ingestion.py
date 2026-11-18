
import json
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "synthetic" / "knowledge.jsonl"
CHROMA_PATH = BASE_DIR / "storage" / "chroma"

COLLECTION_NAME = "senior_knowledge"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

CHUNK_SIZE = 110
CHUNK_OVERLAP = 20


def load_documents():
    documents = []

    with DATA_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                documents.append(json.loads(line))

    if not documents:
        raise ValueError("Knowledge dataset is empty")

    return documents


def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    if not 0 <= overlap < size:
        raise ValueError("Invalid chunk configuration")

    words = text.split()
    chunks = []
    step = size - overlap

    for start in range(0, len(words), step):
        part = words[start:start + size]
        if part:
            chunks.append(" ".join(part))
        if start + size >= len(words):
            break

    return chunks


def prepare_chunks(documents):
    chunks = []

    for doc in documents:
        searchable_text = (
            f"Title: {doc['title']}\n"
            f"Type: {doc['type']}\n"
            f"Context: {doc['context']}\n"
            f"Content: {doc['content']}\n"
            f"Decision: {doc['decision']}\n"
            f"Reasoning: {doc['reasoning']}\n"
            f"Trade-offs: {'; '.join(doc['trade_offs'])}"
        )

        parts = chunk_text(searchable_text)

        for index, part in enumerate(parts):
            chunks.append({
                "id": f"{doc['id']}::chunk::{index}",
                "text": part,
                "metadata": {
                    "source_id": doc["id"],
                    "senior_id": doc["senior_id"],
                    "type": doc["type"],
                    "title": doc["title"],
                    "project": doc["project"],
                    "date": doc["date"],
                    "chunk_index": index,
                    "related_ids": ",".join(doc["related_ids"]),
                },
            })

    return chunks


def ingest():
    print("Loading synthetic knowledge...")
    documents = load_documents()
    chunks = prepare_chunks(documents)

    print(f"Documents: {len(documents)}")
    print(f"Chunks: {len(chunks)}")

    print("Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME, device="cpu")

    texts = [chunk["text"] for chunk in chunks]

    print("Creating embeddings...")
    embeddings = model.encode(
        texts,
        batch_size=16,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))

    # Dedicated local collection: rebuild to avoid stale chunks.
    try:
        client.delete_collection(COLLECTION_NAME)
    except chromadb.errors.NotFoundError:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    collection.add(
        ids=[chunk["id"] for chunk in chunks],
        documents=texts,
        metadatas=[chunk["metadata"] for chunk in chunks],
        embeddings=embeddings.tolist(),
    )

    print("INGESTION COMPLETED")
    print(f"Stored chunks: {collection.count()}")
    print(f"Chroma path: {CHROMA_PATH}")





def ingest_document(file_path: str) -> dict:
    """
    Append a TXT, MD or PDF document to the existing
    senior_knowledge collection without deleting old chunks.

    Re-uploading identical content does not duplicate chunks.
    """
    import hashlib
    from io import BytesIO

    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"Document not found: {path}")

    suffix = path.suffix.lower()
    if suffix not in {".txt", ".md", ".pdf"}:
        raise ValueError("Supported formats: .txt, .md, .pdf")

    raw = path.read_bytes()
    if not raw:
        raise ValueError("Uploaded document is empty")

    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(raw))
        text = "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )
    else:
        text = raw.decode("utf-8-sig")

    if not text.strip():
        raise ValueError("Document contains no extractable text")

    parts = chunk_text(text)
    source_id = "UPLOAD-" + hashlib.sha256(raw).hexdigest()[:20]

    ids = [
        f"{source_id}::chunk::{index}"
        for index in range(len(parts))
    ]

    # Never delete or recreate the collection for uploads.
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    collection = client.get_collection(COLLECTION_NAME)

    existing = set(
        collection.get(ids=ids, include=[])["ids"]
    )

    missing = [
        (index, part)
        for index, part in enumerate(parts)
        if ids[index] not in existing
    ]

    if missing:
        model = SentenceTransformer(MODEL_NAME, device="cpu")
        embeddings = model.encode(
            [part for _, part in missing],
            batch_size=16,
            normalize_embeddings=True,
        )

        collection.add(
            ids=[ids[index] for index, _ in missing],
            documents=[part for _, part in missing],
            metadatas=[
                {
                    "source_id": source_id,
                    "title": path.name,
                    "type": "document",
                    "chunk_index": index,
                }
                for index, _ in missing
            ],
            embeddings=embeddings.tolist(),
        )

    return {
        "source_id": source_id,
        "title": path.name,
        "type": "document",
        "chunks_added": len(missing),
        "total_chunks": collection.count(),
    }


if __name__ == "__main__":
    ingest()
