"""
ALF memory system.

Persistent memory stored in SQLite.
"""

import sqlite3
from pathlib import Path
from datetime import datetime


DATABASE = Path("data/alf.db")


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

    connection.commit()
    connection.close()
