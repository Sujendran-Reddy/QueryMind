import sqlite3
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4


DATABASE_PATH = Path("data/querymind.db")


def initialise_database():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS collections (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


@contextmanager
def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def create_collection(name: str):
    collection_id = str(uuid4())

    with get_connection() as connection:
        connection.execute(
            "INSERT INTO collections (id, name) VALUES (?, ?)",
            (collection_id, name),
        )

        row = connection.execute(
            "SELECT * FROM collections WHERE id = ?",
            (collection_id,),
        ).fetchone()

    return dict(row)


def get_collections():
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM collections ORDER BY created_at DESC"
        ).fetchall()

    return [dict(row) for row in rows]