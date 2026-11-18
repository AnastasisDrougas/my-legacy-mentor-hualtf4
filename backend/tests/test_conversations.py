
import pytest

from app import database
from app.repositories.conversations import (
    add_message,
    create_conversation,
    get_conversation,
    get_messages,
)


@pytest.fixture(autouse=True)
def temporary_database(tmp_path, monkeypatch):
    # Isolate tests from the application database
    db_path = tmp_path / "conversations_test.db"

    monkeypatch.setattr(
        database,
        "get_database_path",
        lambda: db_path,
    )

    database.init_db()


def test_create_conversation():
    conversation_id = create_conversation()

    conversation = get_conversation(conversation_id)

    assert conversation is not None
    assert conversation["id"] == conversation_id


def test_get_unknown_conversation():
    assert get_conversation("unknown-id") is None


def test_add_and_get_messages():
    conversation_id = create_conversation()

    add_message(
        conversation_id,
        "user",
        "What is RAG?",
        mode="ask",
    )

    add_message(
        conversation_id,
        "assistant",
        "RAG combines retrieval and generation.",
        mode="ask",
        sources=[
            {
                "source_id": "DOC-001",
                "title": "RAG Documentation",
                "type": "technical_document",
            }
        ],
    )

    messages = get_messages(conversation_id)

    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["sources"][0]["source_id"] == "DOC-001"


def test_empty_conversation():
    conversation_id = create_conversation()

    assert get_messages(conversation_id) == []


def test_invalid_message_role():
    conversation_id = create_conversation()

    with pytest.raises(ValueError):
        add_message(conversation_id, "invalid", "Hello")


def test_invalid_message_mode():
    conversation_id = create_conversation()

    with pytest.raises(ValueError):
        add_message(conversation_id, "user", "Hello", mode="invalid")


def test_empty_message():
    conversation_id = create_conversation()

    with pytest.raises(ValueError):
        add_message(conversation_id, "user", "   ")


def test_unknown_conversation_message():
    # Foreign keys must reject orphan messages
    with pytest.raises(database.sqlite3.IntegrityError):
        add_message("unknown-id", "user", "Hello")
