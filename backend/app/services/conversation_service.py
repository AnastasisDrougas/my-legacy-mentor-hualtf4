
from app.repositories.conversations import (
    create_conversation,
    get_conversation,
    get_messages,
    list_conversations as repository_list_conversations,
)



def start_conversation() -> dict:
    # Create a new conversation
    conversation_id = create_conversation()
    return get_conversation(conversation_id)


def get_conversation_history(conversation_id: str) -> dict | None:
    # Retrieve conversation and stored messages
    conversation = get_conversation(conversation_id)

    if conversation is None:
        return None

    return {
        **conversation,
        "messages": get_messages(conversation_id),
    }


def list_conversation_history() -> list[dict]:
    # Retrieve available conversations
    return repository_list_conversations()
