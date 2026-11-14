from fastapi import APIRouter, HTTPException

from app.schemas import ChatRequest, ChatResponse
from app.services import ai_service

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        return ai_service.generate_answer(request)

    except ai_service.AIServiceError:
        # Return a safe error without exposing internal details
        raise HTTPException(
            status_code=503,
            detail="AI service is temporarily unavailable"
        )