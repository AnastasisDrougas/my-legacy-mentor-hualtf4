
from fastapi import APIRouter, HTTPException

from app.services.conversation_service import (
    start_conversation,
    get_conversation_history,
    list_conversation_history,
)

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post("", status_code=201)
def create_conversation():
    # Start a new conversation
    return start_conversation()


@router.get("")
def read_conversations():
    # Return the conversation list
    return list_conversation_history()

@router.get("/{conversation_id}")
def read_conversation(conversation_id: str):
    # Return stored messages or 404
    conversation = get_conversation_history(conversation_id)

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    return conversation

