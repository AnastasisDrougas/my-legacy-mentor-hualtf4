import sqlite3

from app import database


def test_database_file_created(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"

    monkeypatch.setattr(
        database,
        "get_database_path",
        lambda: db_path,
    )

    database.init_db()

    assert db_path.exists()


def test_database_connection(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"

    monkeypatch.setattr(
        database,
        "get_database_path",
        lambda: db_path,
    )

    with database.get_db_connection() as connection:
        result = connection.execute(
            "SELECT 1 AS value"
        ).fetchone()

    assert result["value"] == 1


def test_database_rollback(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"

    monkeypatch.setattr(
        database,
        "get_database_path",
        lambda: db_path,
    )

    with database.get_db_connection() as connection:
        connection.execute(
            "CREATE TABLE example (id INTEGER)"
        )

    try:
        with database.get_db_connection() as connection:
            connection.execute(
                "INSERT INTO example VALUES (1)"
            )
            raise ValueError("Test rollback")
    except ValueError:
        pass

    with database.get_db_connection() as connection:
        result = connection.execute(
            "SELECT COUNT(*) AS total FROM example"
        ).fetchone()

    assert result["total"] == 0


def test_foreign_keys_enabled(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"

    monkeypatch.setattr(
        database,
        "get_database_path",
        lambda: db_path,
    )

    with database.get_db_connection() as connection:
        result = connection.execute(
            "PRAGMA foreign_keys"
        ).fetchone()

    assert result[0] == 1