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
            previous_memory_id INTEGER,
            related_memory_ids TEXT
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


def validate_related_memory_ids(related_memory_ids):
    """
    Validate a comma-separated list of related memory IDs.
    """

    if not related_memory_ids:
        return None

    memory_ids = related_memory_ids.split(",")

    for memory_id in memory_ids:
        if not memory_id.isdigit() or int(memory_id) <= 0:
            return False

        if get_memory(int(memory_id)) is None:
            return False

    return ",".join(memory_ids)


def remember(
    category: str,
    content: str,
    previous_memory_id=None,
    related_memory_ids=None,
):
    """
    Store a memory in ALF's database.
    """

    related_memory_ids = validate_related_memory_ids(related_memory_ids)

    if related_memory_ids is False:
        return False

    with get_connection() as connection:
        cursor = connection.cursor()

        created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(

        """
        INSERT INTO memories (
            created,
            category,
            status,
            content,
            previous_memory_id,
            related_memory_ids
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            created,
            category,
            "active",
            content,
            previous_memory_id,
            related_memory_ids,
        ),
    )

    return True


def get_memories(options=None):
    """
    Retrieve ALF memories using query options.
    Archived memories are not displayed by default.
    """

    if options is None:
        options = get_memory_query_options()

    category = options["category"]
    include_archived = options["include_archived"]

    memories = []

    with get_connection() as connection:
        cursor = connection.cursor()

        if category and include_archived:
            cursor.execute(
                """
                SELECT id, created, category, status, content,
                previous_memory_id, related_memory_ids
                FROM memories
                WHERE category = ?
                ORDER BY id
                """,
                (category,),
            )

        elif category:
            cursor.execute(
                """
                SELECT id, created, category, status, content,
                previous_memory_id, related_memory_ids
                FROM memories
                WHERE category = ? AND status = 'active'
                ORDER BY id
                """,
                (category,),
            )

        elif include_archived:
            cursor.execute(
                """
                SELECT id, created, category, status, content,
                previous_memory_id, related_memory_ids
                FROM memories
                ORDER BY id
                """
            )

        else:
            cursor.execute(
                """
                SELECT id, created, category, status, content,
                previous_memory_id, related_memory_ids
                FROM memories
                WHERE status = 'active'
                ORDER BY id
                """
            )

        rows = cursor.fetchall()

        for row in rows:
            memories.append(
                {
                    "id": row[0],
                    "created": row[1],
                    "category": row[2],
                    "status": row[3],
                    "content": row[4],
                    "previous_memory_id": row[5],
                    "related_memory_ids": row[6],
                }
            )

    return memories


def search_memories(term, options=None):
    """
    Search memories by content using query options.
    """

    if options is None:
        options = get_memory_query_options()

    category = options["category"]
    include_archived = options["include_archived"]

    memories = []

    with get_connection() as connection:
        cursor = connection.cursor()

        query = """
            SELECT id, created, category, status, content,
            previous_memory_id, related_memory_ids
            FROM memories
            WHERE content LIKE ?
        """

        parameters = [f"%{term}%"]

        if not include_archived:
            query += " AND status = 'active'"

        if category:
            query += " AND category = ?"
            parameters.append(category)

        query += " ORDER BY id"

        cursor.execute(query, parameters)

        rows = cursor.fetchall()

    for row in rows:
        memories.append(
            {
                "id": row[0],
                "created": row[1],
                "category": row[2],
                "status": row[3],
                "content": row[4],
                "previous_memory_id": row[5],
                "related_memory_ids": row[6],
            }
        )

    return memories


def get_memory(memory_id: int):
    """
    Retrieve a single memory by ID.
    """

    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, created, category, status, content,
            previous_memory_id, related_memory_ids
            FROM memories
            WHERE id = ?
            """,
            (memory_id,),
        )

        row = cursor.fetchone()

    if row is None:
        return None

    return {
        "id": row[0],
        "created": row[1],
        "category": row[2],
        "status": row[3],
        "content": row[4],
        "previous_memory_id": row[5],
        "related_memory_ids": row[6],
    }


def get_related_memories(memory_id: int):
    """
    Retrieve the memories directly related to a memory.

    Relationships are deliberately limited to one level. This function
    retrieves the memories named by the stored relationship IDs but does
    not follow relationships belonging to those memories.
    """

    memory = get_memory(memory_id)

    if memory is None or not memory.get("related_memory_ids"):
        return []

    related_memories = []

    for related_id in memory["related_memory_ids"].split(","):
        related_memory = get_memory(int(related_id))

        if related_memory is not None:
            related_memories.append(related_memory)

    return related_memories


def get_memory_history(memory_id: int):
    """
    Retrieve the history chain for a memory.
    """

    history = []

    memory = get_memory(memory_id)

    while memory:
        history.insert(0, memory)

        previous_id = memory["previous_memory_id"]

        if previous_id is None:
            break

        memory = get_memory(previous_id)

    return history


def archive_memory(memory_id: int):
    """
    Mark a memory as archived.
    """

    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE memories
            SET status = 'archived'
            WHERE id = ?
            """,
            (memory_id,),
        )


def forget_memory(memory_id):
    """
    Forget a memory while preserving its identity.
    """

    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE memories
            SET status = 'forgotten',
                content = '[forgotten]'
            WHERE id = ?
            """,
            (memory_id,),
        )


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
