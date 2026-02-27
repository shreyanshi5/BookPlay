import os
import sqlite3
from typing import Iterable, Dict

DB_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(DB_DIR, "audiobook.db")


def get_db() -> sqlite3.Connection:
    """
    Return a SQLite connection with row factory configured to return dict-like rows.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    Initialize the SQLite database with required tables if they do not exist.
    """
    os.makedirs(DB_DIR, exist_ok=True)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS files (
            id TEXT PRIMARY KEY,
            filename TEXT,
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS characters (
            name TEXT PRIMARY KEY,
            assigned_voice TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS outputs (
            id TEXT PRIMARY KEY,
            file_id TEXT NOT NULL,
            audio_path TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (file_id) REFERENCES files (id)
        )
        """
    )

    conn.commit()
    conn.close()


def upsert_character_voices(conn: sqlite3.Connection, mappings: Dict[str, str]) -> None:
    """
    Insert or update character->voice mappings.
    """
    cursor = conn.cursor()
    for name, voice_id in mappings.items():
        cursor.execute(
            """
            INSERT INTO characters (name, assigned_voice)
            VALUES (?, ?)
            ON CONFLICT(name) DO UPDATE SET assigned_voice=excluded.assigned_voice
            """,
            (name, voice_id),
        )
    conn.commit()


def load_character_voices(conn: sqlite3.Connection, names: Iterable[str]) -> Dict[str, str]:
    """
    Load existing character->voice mappings for the given character names.
    """
    placeholders = ",".join("?" for _ in names)
    if not placeholders:
        return {}

    cursor = conn.cursor()
    cursor.execute(
        f"SELECT name, assigned_voice FROM characters WHERE name IN ({placeholders})",
        tuple(names),
    )
    rows = cursor.fetchall()
    return {row["name"]: row["assigned_voice"] for row in rows}

