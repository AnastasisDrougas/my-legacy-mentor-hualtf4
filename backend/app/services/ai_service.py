from functools import lru_cache

from app.schemas import ChatRequest, ChatResponse


class AIServiceError(Exception):
    pass


@lru_cache(maxsize=1)
def get_pipeline():
    # Reuse the RAG pipeline across requests
    from ai.rag_pipeline import RAGPipeline

    return RAGPipeline()


def generate_answer(request: ChatRequest) -> ChatResponse:
    try:
        result = get_pipeline().ask(
            question=request.question,
            top_k=5,
            mode=request.mode,
        )

        return ChatResponse(
            answer=result["answer"],
            mode=request.mode,
            sources=result["sources"],
        )

    except Exception as exc:
        # Hide internal AI errors from API responses
        raise AIServiceError("AI processing failed") from exc