
import pytest

from app import database
from app.repositories.conversations import add_message
from app.services.conversation_service import (
    start_conversation,
    get_conversation_history,
)


@pytest.fixture(autouse=True)
def temporary_database(tmp_path, monkeypatch):
    # Use a temporary database for each test
    db_path = tmp_path / "service_test.db"

    monkeypatch.setattr(
        database,
        "get_database_path",
        lambda: db_path,
    )

    database.init_db()


def test_start_conversation():
    conversation = start_conversation()

    assert conversation["id"]
    assert conversation["created_at"]


def test_get_conversation_history():
    conversation = start_conversation()
    conversation_id = conversation["id"]

    add_message(
        conversation_id,
        "user",
        "What is RAG?",
        mode="ask",
    )

    history = get_conversation_history(conversation_id)

    assert history["id"] == conversation_id
    assert len(history["messages"]) == 1
    assert history["messages"][0]["content"] == "What is RAG?"


def test_unknown_conversation_history():
    assert get_conversation_history("unknown-id") is None
