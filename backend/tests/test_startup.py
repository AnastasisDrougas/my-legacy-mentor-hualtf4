
import sqlite3

from fastapi.testclient import TestClient

from app import database
from app.main import app


def test_database_initialized_on_startup(tmp_path, monkeypatch):
    # Use an isolated SQLite database
    db_path = tmp_path / "startup_test.db"

    monkeypatch.setattr(
        database,
        "get_database_path",
        lambda: db_path,
    )

    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200

    assert db_path.exists()

    connection = sqlite3.connect(db_path)

    try:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
    finally:
        connection.close()

    assert "conversations" in tables
    assert "messages" in tables
