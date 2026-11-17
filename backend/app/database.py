
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from app.config import settings


def get_database_path() -> Path:
    # Resolve relative paths from the backend directory
    path = Path(settings.DATABASE_PATH)

    if not path.is_absolute():
        path = Path(__file__).resolve().parents[1] / path

    return path


@contextmanager
def get_db_connection():
    # Manage transactions and close connections safely
    db_path = get_database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(str(db_path), timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()



def init_db():
    # Initialize conversation and message tables
    with get_db_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL
                    CHECK (role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                mode TEXT
                    CHECK (mode IS NULL OR mode IN ('ask', 'mentor')),
                sources TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id)
                    REFERENCES conversations(id)
                    ON DELETE CASCADE
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_conversation
            ON messages(conversation_id, created_at)
        """)

