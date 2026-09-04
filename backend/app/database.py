import sqlite3
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4


DATABASE_PATH = Path("data/querymind.db")


@contextmanager
def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialise_database():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS collections (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                collection_id TEXT NOT NULL,
                name TEXT NOT NULL,
                page_count INTEGER NOT NULL,
                character_count INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (collection_id)
                    REFERENCES collections(id)
                    ON DELETE CASCADE
            );
            """
        )


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


def collection_exists(collection_id: str) -> bool:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id FROM collections WHERE id = ?",
            (collection_id,),
        ).fetchone()

    return row is not None


def create_document(
    collection_id: str,
    name: str,
    page_count: int,
    character_count: int,
):
    document_id = str(uuid4())

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO documents (
                id,
                collection_id,
                name,
                page_count,
                character_count,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                document_id,
                collection_id,
                name,
                page_count,
                character_count,
                "extracted",
            ),
        )

        row = connection.execute(
            "SELECT * FROM documents WHERE id = ?",
            (document_id,),
        ).fetchone()

    return dict(row)


def get_documents(collection_id: str):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM documents
            WHERE collection_id = ?
            ORDER BY created_at DESC
            """,
            (collection_id,),
        ).fetchall()

    return [dict(row) for row in rows]