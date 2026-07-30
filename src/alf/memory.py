"""
ALF memory system.

Persistent memory stored in SQLite.
"""

import sqlite3
from pathlib import Path
from datetime import datetime


DATABASE = Path("data/alf.db")

VALID_MEMORY_CATEGORIES = [
    "note",
    "fact",
    "decision",
    "preference",
]

def get_connection():
    """
    Open a connection to ALF's memory database.
    """

    DATABASE.parent.mkdir(exist_ok=True)

    return sqlite3.connect(DATABASE)


def initialise_database():
    """
    Create ALF memory tables if they do not exist.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created TEXT NOT NULL,
            category TEXT NOT NULL,
            content TEXT NOT NULL
        )
        """
    )

def get_memory_categories():
    """
    Return valid memory categories.
    """

    return VALID_MEMORY_CATEGORIES


def remember(category: str, content: str):
    """
    Store a memory in ALF's database.
    """

    connection = get_connection()

    cursor = connection.cursor()

    created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        """
        INSERT INTO memories (created, category, content)
        VALUES (?, ?, ?)
        """,
        (created, category, content),
    )

    connection.commit()
    connection.close()


def get_memories():
    """
    Retrieve all ALF memories.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, created, category, content
        FROM memories
        ORDER BY id
        """
    )

    memories = cursor.fetchall()

    connection.close()

    return memories
    connection.commit()
    connection.close()

