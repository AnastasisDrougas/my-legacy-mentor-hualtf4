
from fastapi import APIRouter, Header, HTTPException, Response

from app.repositories.conversations import (
    get_conversation,
    save_chat_exchange,
)
from app.schemas import ChatRequest, ChatResponse
from app.services import ai_service

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    response: Response,
    conversation_id: str | None = Header(
        default=None,
        alias="X-Conversation-ID",
    ),
):
    # Validate an existing conversation before calling AI
    if (
        conversation_id is not None
        and get_conversation(conversation_id) is None
    ):
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    try:
        result = ai_service.generate_answer(request)

    except ai_service.AIServiceError:
        raise HTTPException(
            status_code=503,
            detail="AI service is temporarily unavailable",
        )

    # Persist the successful exchange
    saved_id = save_chat_exchange(
        question=request.question,
        answer=result.answer,
        mode=result.mode,
        sources=[
            source.model_dump()
            for source in result.sources
        ],
        conversation_id=conversation_id,
    )

    response.headers["X-Conversation-ID"] = saved_id

    return result
