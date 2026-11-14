from app.schemas import ChatRequest, ChatResponse


class AIServiceError(Exception):
    pass


def generate_answer(request: ChatRequest) -> ChatResponse:
    # Temporary mock until the real AI module is integrated
    return ChatResponse(
        answer=f"Mock response to: {request.question}",
        mode=request.mode,
        sources=[]
    )