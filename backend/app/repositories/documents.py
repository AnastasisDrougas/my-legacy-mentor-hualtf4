
from datetime import datetime, timezone
from uuid import uuid4

from app.database import get_db_connection


VALID_STATUSES = {
    "uploaded",
    "processing",
    "ready",
    "failed",
}


def create_document(
    filename: str,
    storage_path: str,
    content_type: str,
    size_bytes: int,
) -> dict:
    # Store document metadata
    if not filename.strip() or not storage_path.strip():
        raise ValueError("Filename and storage path are required")

    if not content_type.strip() or size_bytes < 0:
        raise ValueError("Invalid document metadata")

    document_id = str(uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    with get_db_connection() as connection:
        connection.execute(
            """
            INSERT INTO documents (
                id, filename, storage_path,
                content_type, size_bytes, status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document_id,
                filename,
                storage_path,
                content_type,
                size_bytes,
                "uploaded",
                created_at,
            ),
        )

    return get_document(document_id)


def get_document(document_id: str) -> dict | None:
    # Retrieve one document
    with get_db_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM documents
            WHERE id = ?
            """,
            (document_id,),
        ).fetchone()

    return dict(row) if row else None


def update_document_status(
    document_id: str,
    status: str,
    error_message: str | None = None,
) -> bool:
    # Update an existing document status
    if status not in VALID_STATUSES:
        raise ValueError("Invalid document status")

    with get_db_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE documents
            SET status = ?, error_message = ?
            WHERE id = ?
            """,
            (status, error_message, document_id),
        )

        return cursor.rowcount > 0
