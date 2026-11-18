
from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    HTTPException,
    UploadFile,
)

from app.repositories.documents import get_document
from app.schemas import DocumentResponse
from app.services import ingestion_service
from app.services.document_service import (
    DocumentValidationError,
    store_document,
)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("", response_model=DocumentResponse, status_code=201)
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    try:
        document = store_document(file)
    except DocumentValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    finally:
        file.file.close()

    background_tasks.add_task(
        ingestion_service.process_document,
        document["id"],
    )

    return document


@router.get("/{document_id}", response_model=DocumentResponse)
def read_document(document_id: str):
    document = get_document(document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return document
