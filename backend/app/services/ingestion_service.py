
import inspect
import logging

from app.repositories.documents import (
    get_document,
    update_document_status,
)

logger = logging.getLogger(__name__)


def process_document(document_id: str) -> None:
    document = get_document(document_id)

    if document is None:
        raise ValueError("Document not found")

    update_document_status(document_id, "processing")

    try:
        from ai.ingestion import ingest_document

        # Support both ingestion interface versions
        parameters = inspect.signature(ingest_document).parameters

        if "title" in parameters:
            result = ingest_document(
                document["storage_path"],
                title=document["filename"],
            )
        else:
            result = ingest_document(document["storage_path"])

        logger.info(
            "Document %s indexed: %s chunks added",
            document_id,
            result["chunks_added"],
        )

        update_document_status(document_id, "ready")

    except Exception:
        logger.exception(
            "Document ingestion failed for %s",
            document_id,
        )
        update_document_status(
            document_id,
            "failed",
            "Document ingestion failed",
        )
