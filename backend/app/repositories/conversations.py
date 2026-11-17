
import json
from datetime import datetime, timezone
from uuid import uuid4

from app.database import get_db_connection


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_conversation() -> str:
    # Create and return a conversation ID
    conversation_id = str(uuid4())

    with get_db_connection() as connection:
        connection.execute(
            """
            INSERT INTO conversations (id, created_at)
            VALUES (?, ?)
            """,
            (conversation_id, utc_now()),
        )

    return conversation_id


def get_conversation(conversation_id: str):
    with get_db_connection() as connection:
        row = connection.execute(
            """
            SELECT id, created_at
            FROM conversations
            WHERE id = ?
            """,
            (conversation_id,),
        ).fetchone()

    return dict(row) if row else None


def add_message(
    conversation_id: str,
    role: str,
    content: str,
    mode: str | None = None,
    sources: list | None = None,
) -> str:
    # Store a message in an existing conversation
    if role not in ("user", "assistant"):
        raise ValueError("Invalid message role")

    if mode not in (None, "ask", "mentor"):
        raise ValueError("Invalid chat mode")

    if not content.strip():
        raise ValueError("Message content cannot be empty")

    message_id = str(uuid4())

    with get_db_connection() as connection:
        connection.execute(
            """
            INSERT INTO messages
                (id, conversation_id, role, content,
                 mode, sources, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message_id,
                conversation_id,
                role,
                content,
                mode,
                json.dumps(sources if sources is not None else []),
                utc_now(),
            ),
        )

    return message_id


def get_messages(conversation_id: str) -> list[dict]:
    # Retrieve messages in insertion order
    with get_db_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, conversation_id, role, content,
                   mode, sources, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at, rowid
            """,
            (conversation_id,),
        ).fetchall()

    messages = []

    for row in rows:
        message = dict(row)
        message["sources"] = json.loads(message["sources"])
        messages.append(message)

    return messages

def save_chat_exchange(
    question: str,
    answer: str,
    mode: str,
    sources: list[dict],
    conversation_id: str | None = None,
) -> str:
    # Save both messages in one transaction
    if mode not in ("ask", "mentor"):
        raise ValueError("Invalid chat mode")

    if not question.strip() or not answer.strip():
        raise ValueError("Messages cannot be empty")

    conversation_id = conversation_id or str(uuid4())

    with get_db_connection() as connection:
        existing = connection.execute(
            "SELECT 1 FROM conversations WHERE id = ?",
            (conversation_id,),
        ).fetchone()

        if existing is None:
            connection.execute(
                """
                INSERT INTO conversations (id, created_at)
                VALUES (?, ?)
                """,
                (conversation_id, utc_now()),
            )

        timestamp = utc_now()

        for role, content, message_sources in (
            ("user", question, []),
            ("assistant", answer, sources),
        ):
            connection.execute(
                """
                INSERT INTO messages
                    (id, conversation_id, role, content,
                     mode, sources, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid4()),
                    conversation_id,
                    role,
                    content,
                    mode,
                    json.dumps(message_sources),
                    timestamp,
                ),
            )

    return conversation_id


def list_conversations() -> list[dict]:
    # Return conversations ordered by newest first
    with get_db_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, created_at
            FROM conversations
            ORDER BY created_at DESC, rowid DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]
