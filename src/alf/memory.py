"""
ALF memory system.

Persistent memory stored in SQLite.
"""

import sqlite3
from datetime import datetime
from .paths import get_data_directory


DATABASE = get_data_directory() / "alf.db"

VALID_MEMORY_CATEGORIES = [
    "note",
    "fact",
    "decision",
    "preference",
]


def initialise_database(connection):
    """
    Create ALF memory tables if they do not exist.
    """

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created TEXT NOT NULL,
            category TEXT NOT NULL,
            content TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            previous_memory_id INTEGER
        )
        """
    )

    connection.commit()


def get_connection():
    """
    Open a connection to ALF's memory database.

    Ensures the database structure exists.
    """

    DATABASE.parent.mkdir(exist_ok=True)

    connection = sqlite3.connect(DATABASE)

    initialise_database(connection)

    return connection


def get_memory_categories():
    """
    Return valid memory categories.
    """

    return VALID_MEMORY_CATEGORIES


def get_memory_query_options():
    """
    Return default memory query options.
    """

    return {
        "category": None,
        "include_archived": False,
        "group": None,
    }


def remember(category: str, content: str, previous_memory_id=None):
    """
    Store a memory in ALF's database.
    """

    connection = get_connection()

    cursor = connection.cursor()

    created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        """
        INSERT INTO memories (
            created,
            category,
            status,
            content,
            previous_memory_id
    )
        VALUES (?, ?, ?, ?, ?)
        """,
        (created, category, "active", content, previous_memory_id),
    )

    connection.commit()
    connection.close()


def get_memories(options=None):
    """
    Retrieve ALF memories using query options.
    Archived memories are not displayed by default.
    """

    if options is None:
        options = get_memory_query_options()

    category = options["category"]
    include_archived = options["include_archived"]

    connection = get_connection()
    cursor = connection.cursor()

    if category and include_archived:
        cursor.execute(
            """
            SELECT id, created, category, status, content, previous_memory_id
            FROM memories
            WHERE category = ?
            ORDER BY id
            """,
            (category,),
        )

    elif category:
        cursor.execute(
            """
            SELECT id, created, category, status, content, previous_memory_id
            FROM memories
            WHERE category = ? AND status = 'active'
            ORDER BY id
            """,
            (category,),
        )

    elif include_archived:
        cursor.execute(
            """
            SELECT id, created, category, status, content, previous_memory_id
            FROM memories
            ORDER BY id
            """
        )

    else:
        cursor.execute(
            """
            SELECT id, created, category, status, content, previous_memory_id
            FROM memories
            WHERE status = 'active'
            ORDER BY id
            """
        )

    rows = cursor.fetchall()

    memories = []

    for row in rows:
        memories.append(
            {
                "id": row[0],
                "created": row[1],
                "category": row[2],
                "status": row[3],
                "content": row[4],
                "previous_memory_id": row[5],
            }
        )

    connection.close()

    return memories


def get_memory(memory_id: int):
    """
    Retrieve a single memory by ID.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, created, category, status, content, previous_memory_id
        FROM memories
        WHERE id = ?
        """,
        (memory_id,),
    )

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    return {
        "id": row[0],
        "created": row[1],
        "category": row[2],
        "status": row[3],
        "content": row[4],
        "previous_memory_id": row[5],
    }


def archive_memory(memory_id: int):
    """
    Mark a memory as archived.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE memories
        SET status = 'archived'
        WHERE id = ?
        """,
        (memory_id,),
    )

    connection.commit()
    connection.close()


def get_memory_information():
    """
    Return information about ALF's memory system.
    """

    memories = get_memories()

    information = {}

    information["total_memories"] = len(memories)

    categories = []

    for memory in memories:
        category = memory["category"]

        if category not in categories:
            categories.append(category)

    information["categories"] = categories

    return information


def get_capability():
    """
    Return memory capability information.
    """

    return {
        "id": "memory",
        "name": "Persistent memory",
        "description": "SQLite-backed memory storage",
        "details": get_memory_information(),
    }
