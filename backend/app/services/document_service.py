
import os
from pathlib import Path
from uuid import uuid4

from app.repositories.documents import create_document


MAX_FILE_SIZE = 5 * 1024 * 1024

ALLOWED_TYPES = {
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".pdf": "application/pdf",
}


class DocumentValidationError(Exception):
    pass


def get_upload_directory() -> Path:
    # Resolve uploads relative to backend
    default_path = Path(__file__).resolve().parents[2] / "data" / "uploads"
    return Path(os.getenv("UPLOAD_DIR", str(default_path)))


def store_document(file) -> dict:
    # Validate file type before saving
    filename = Path(file.filename or "").name
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_TYPES:
        raise DocumentValidationError("Unsupported file type")

    if file.content_type != ALLOWED_TYPES[extension]:
        raise DocumentValidationError("Invalid content type")

    upload_dir = get_upload_directory()
    upload_dir.mkdir(parents=True, exist_ok=True)

    storage_path = upload_dir / f"{uuid4().hex}{extension}"
    size = 0

    try:
        with storage_path.open("xb") as destination:
            while chunk := file.file.read(64 * 1024):
                size += len(chunk)

                if size > MAX_FILE_SIZE:
                    raise DocumentValidationError(
                        "File exceeds the 5 MB limit"
                    )

                destination.write(chunk)

        if size == 0:
            raise DocumentValidationError("Empty files are not allowed")

        # Verify PDF signature
        if extension == ".pdf":
            with storage_path.open("rb") as saved:
                if saved.read(5) != b"%PDF-":
                    raise DocumentValidationError("Invalid PDF file")

        # Store metadata after successful file validation
        return create_document(
            filename=filename,
            storage_path=str(storage_path),
            content_type=file.content_type,
            size_bytes=size,
        )

    except Exception:
        storage_path.unlink(missing_ok=True)
        raise
