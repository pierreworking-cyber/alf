"""
ALF's persistent memory data layer.

This module manages the SQLite-backed store used to give ALF
persistent memory across sessions. It is responsible for creating
and maintaining the memory database, storing and retrieving memory
entries, searching and filtering memories, and managing their
lifecycle through active, archived, and forgotten states.

It also manages relationships between memories and their revision
history. Presentation and command-handling concerns remain outside
this module; its responsibility is to provide the underlying memory
data and memory-system information to the rest of ALF.
"""

import sqlite3
from datetime import datetime

from .paths import get_data_directory

DATABASE = get_data_directory() / "alf.db"


SCHEMA_VERSION = 4

VALID_MEMORY_CATEGORIES = [
    "note",
    "fact",
    "decision",
    "preference",
]


def initialise_database(connection):
    """
    Create the memory schema and apply any required schema migrations.

    The supplied SQLite connection is updated in place and committed
    before the function returns.

    Args:
        connection: An open SQLite database connection.
    """

    cursor = connection.cursor()

    version = connection.execute(
        "PRAGMA user_version"
    ).fetchone()[0]

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

    cursor.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts
        USING fts5(
            content,
            content='memories',
            content_rowid='id'
        )
        """
    )

    if version < 2:
        cursor.execute(
            """
            INSERT INTO memory_fts (rowid, content)
            SELECT id, content
            FROM memories
            """
        )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS mindmaps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            project TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created TEXT NOT NULL,
            modified TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS mindmap_documents (
            mindmap_id INTEGER PRIMARY KEY,
            content TEXT NOT NULL,
            FOREIGN KEY (mindmap_id)
                REFERENCES mindmaps(id)
                ON DELETE CASCADE
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS mindmap_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL DEFAULT 'active',
            created TEXT NOT NULL,
            modified TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS mindmap_projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created TEXT NOT NULL,
            modified TEXT NOT NULL,
            FOREIGN KEY (category_id)
                REFERENCES mindmap_categories(id)
        )
        """
    )

    connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    connection.commit()


def get_connection():
    """
    Open and initialise a connection to ALF's memory database.

    The database directory and schema are created when necessary.

    Returns:
        An initialised SQLite database connection.
    """

    DATABASE.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE)

    connection.execute("PRAGMA foreign_keys = ON")

    initialise_database(connection)

    return connection


def create_mindmap_category(name: str):
    """
    Create a new mind map category.

    Args:
        name: The category name.

    Returns:
        The ID of the newly created category.
    """

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO mindmap_categories (
                name,
                status,
                created,
                modified
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                name,
                "active",
                now,
                now,
            ),
        )

        return cursor.lastrowid


def get_mindmap_categories():
    """
    Return all mind map categories ordered by ID.

    Returns:
        A list of category dictionaries.
    """

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, name, status, created, modified
            FROM mindmap_categories
            ORDER BY id
            """
        ).fetchall()

    return [
        {
            "id": row[0],
            "name": row[1],
            "status": row[2],
            "created": row[3],
            "modified": row[4],
        }
        for row in rows
    ]


def update_mindmap_category(
    category_id: int,
    name: str,
    status: str,
):
    """
    Update an existing mind map category.

    Returns:
        ``True`` when the category is updated, otherwise ``False``.
    """

    with get_connection() as connection:
        category = connection.execute(
            """
            SELECT id
            FROM mindmap_categories
            WHERE id = ?
            """,
            (category_id,),
        ).fetchone()

        if category is None:
            return False

        modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        connection.execute(
            """
            UPDATE mindmap_categories
            SET name = ?,
                status = ?,
                modified = ?
            WHERE id = ?
            """,
            (
                name,
                status,
                modified,
                category_id,
            ),
        )

    return True


def archive_mindmap_category(category_id: int):
    """
    Archive an existing mind map category.

    Returns:
        ``True`` when the category is archived, otherwise ``False``.
    """

    with get_connection() as connection:
        category = connection.execute(
            """
            SELECT id
            FROM mindmap_categories
            WHERE id = ?
            """,
            (category_id,),
        ).fetchone()

        if category is None:
            return False

        modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        connection.execute(
            """
            UPDATE mindmap_categories
            SET status = 'archived',
                modified = ?
            WHERE id = ?
            """,
            (modified, category_id),
        )

    return True


def delete_mindmap_category(category_id: int):
    """
    Delete an existing mind map category.

    Returns:
        ``True`` when the category is deleted, otherwise ``False``.
    """

    with get_connection() as connection:
        category = connection.execute(
            """
            SELECT id
            FROM mindmap_categories
            WHERE id = ?
            """,
            (category_id,),
        ).fetchone()

        if category is None:
            return False

        connection.execute(
            """
            DELETE FROM mindmap_categories
            WHERE id = ?
            """,
            (category_id,),
        )

    return True


def create_mindmap_project(category_id: int, name: str):
    """
    Create a new mind map project within a category.

    Returns:
        The new project ID, or ``False`` when the category does not exist.
    """

    with get_connection() as connection:
        category = connection.execute(
            """
            SELECT id
            FROM mindmap_categories
            WHERE id = ?
            """,
            (category_id,),
        ).fetchone()

        if category is None:
            return False

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO mindmap_projects (
                category_id,
                name,
                status,
                created,
                modified
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                category_id,
                name,
                "active",
                now,
                now,
            ),
        )

        return cursor.lastrowid


def get_mindmap_projects():
    """
    Return all mind map projects ordered by ID.

    Returns:
        A list of project dictionaries.
    """

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, category_id, name, status, created, modified
            FROM mindmap_projects
            ORDER BY id
            """
        ).fetchall()

    return [
        {
            "id": row[0],
            "category_id": row[1],
            "name": row[2],
            "status": row[3],
            "created": row[4],
            "modified": row[5],
        }
        for row in rows
    ]


def update_mindmap_project(
    project_id: int,
    category_id: int,
    name: str,
    status: str,
):
    """
    Update an existing mind map project.

    Returns:
        ``True`` when the project is updated, otherwise ``False``.
    """

    with get_connection() as connection:
        project = connection.execute(
            """
            SELECT id
            FROM mindmap_projects
            WHERE id = ?
            """,
            (project_id,),
        ).fetchone()

        if project is None:
            return False

        category = connection.execute(
            """
            SELECT id
            FROM mindmap_categories
            WHERE id = ?
            """,
            (category_id,),
        ).fetchone()

        if category is None:
            return False

        modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        connection.execute(
            """
            UPDATE mindmap_projects
            SET category_id = ?,
                name = ?,
                status = ?,
                modified = ?
            WHERE id = ?
            """,
            (
                category_id,
                name,
                status,
                modified,
                project_id,
            ),
        )

    return True


def archive_mindmap_project(project_id: int):
    """
    Archive an existing mind map project.

    Returns:
        ``True`` when the project is archived, otherwise ``False``.
    """

    with get_connection() as connection:
        project = connection.execute(
            """
            SELECT id
            FROM mindmap_projects
            WHERE id = ?
            """,
            (project_id,),
        ).fetchone()

        if project is None:
            return False

        modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        connection.execute(
            """
            UPDATE mindmap_projects
            SET status = 'archived',
                modified = ?
            WHERE id = ?
            """,
            (modified, project_id),
        )

    return True


def delete_mindmap_project(project_id: int):
    """
    Permanently delete an existing mind map project.

    Returns:
        ``True`` when the project is deleted, otherwise ``False``.
    """

    with get_connection() as connection:
        project = connection.execute(
            """
            SELECT id
            FROM mindmap_projects
            WHERE id = ?
            """,
            (project_id,),
        ).fetchone()

        if project is None:
            return False

        connection.execute(
            """
            DELETE FROM mindmap_projects
            WHERE id = ?
            """,
            (project_id,),
        )

    return True


def create_mindmap(category: str, project: str, content: str):
    """
    Create a new mind map and its associated document.

    Returns:
        The new mind map ID.
    """

    created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO mindmaps (
                category,
                project,
                status,
                created,
                modified
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                category,
                project,
                "active",
                created,
                created,
            ),
        )

        mindmap_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO mindmap_documents (
                mindmap_id,
                content
            )
            VALUES (?, ?)
            """,
            (mindmap_id, content),
        )

    return mindmap_id


def get_mindmap(mindmap_id: int):
    """
    Retrieve a mind map and its associated document.

    Returns:
        The mind map as a dictionary, or ``None`` if it does not exist.
    """

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                m.id,
                m.category,
                m.project,
                m.status,
                m.created,
                m.modified,
                d.content
            FROM mindmaps AS m
            JOIN mindmap_documents AS d
                ON d.mindmap_id = m.id
            WHERE m.id = ?
            """,
            (mindmap_id,),
        ).fetchone()

    if row is None:
        return None

    return {
        "id": row[0],
        "category": row[1],
        "project": row[2],
        "status": row[3],
        "created": row[4],
        "modified": row[5],
        "content": row[6],
    }


def get_mindmaps():
    """
    Retrieve all mind maps.

    Returns:
        A list of mind maps ordered by ID.
    """

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                m.id,
                m.category,
                m.project,
                m.status,
                m.created,
                m.modified,
                d.content
            FROM mindmaps AS m
            JOIN mindmap_documents AS d
                ON d.mindmap_id = m.id
            ORDER BY m.id
            """
        ).fetchall()

    return [
        {
            "id": row[0],
            "category": row[1],
            "project": row[2],
            "status": row[3],
            "created": row[4],
            "modified": row[5],
            "content": row[6],
        }
        for row in rows
    ]


def update_mindmap(
    mindmap_id: int,
    category: str,
    project: str,
    status: str,
    content: str,
):
    """
    Update a mind map and its associated document.

    The modified timestamp is refreshed whenever the mind map is
    updated.

    Returns:
        ``True`` when the mind map is updated, otherwise ``False`` when
        the mind map does not exist.
    """

    with get_connection() as connection:
        existing = connection.execute(
            """
            SELECT id
            FROM mindmaps
            WHERE id = ?
            """,
            (mindmap_id,),
        ).fetchone()

        if existing is None:
            return False

        modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        connection.execute(
            """
            UPDATE mindmaps
            SET category = ?,
                project = ?,
                status = ?,
                modified = ?
            WHERE id = ?
            """,
            (
                category,
                project,
                status,
                modified,
                mindmap_id,
            ),
        )

        connection.execute(
            """
            UPDATE mindmap_documents
            SET content = ?
            WHERE mindmap_id = ?
            """,
            (content, mindmap_id),
        )

    return True


def archive_mindmap(mindmap_id: int):
    """
    Mark a mind map as archived.

    Returns:
        ``True`` when the mind map is archived, otherwise ``False``
        when it does not exist.
    """

    with get_connection() as connection:
        result = connection.execute(
            """
            UPDATE mindmaps
            SET status = 'archived',
                modified = ?
            WHERE id = ?
            """,
            (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                mindmap_id,
            ),
        )

    return result.rowcount > 0


def delete_mindmap(mindmap_id: int):
    """
    Permanently delete a mind map and its associated document.

    Returns:
        ``True`` when the mind map is deleted, otherwise ``False``
        when it does not exist.
    """

    with get_connection() as connection:
        result = connection.execute(
            """
            DELETE FROM mindmaps
            WHERE id = ?
            """,
            (mindmap_id,),
        )

    return result.rowcount > 0


def get_memory_categories():
    """
    Return a copy of ALF's valid memory categories.

    Returns:
        A list of supported memory category names.
    """

    return VALID_MEMORY_CATEGORIES.copy()


def get_memory_query_options():
    """
    Create the default options used when querying memories.

    Returns:
        A dictionary containing the default category, archive, and
        grouping options.
    """

    return {
        "category": None,
        "include_archived": False,
        "group": None,
    }


def validate_related_memory_ids(related_memory_ids):
    """
    Validate and normalise a comma-separated list of memory IDs.

    Each referenced memory must exist. An empty value means that no
    relationships were supplied.

    Args:
        related_memory_ids: A comma-separated string of memory IDs.

    Returns:
        The validated ID string, ``None`` when no IDs were supplied, or
        ``False`` when the value is invalid.
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


def relate_memory(memory_id: int, related_memory_ids):
    """
    Add relationships to an existing memory.

    Relationships are directional and additive. Existing relationships
    are preserved and duplicate relationship IDs are ignored.
    """

    memory = get_memory(memory_id)

    if memory is None:
        return False

    if not related_memory_ids:
        return False

    new_ids = related_memory_ids.split(",")

    for related_id in new_ids:
        if (
            not related_id.isdigit()
            or int(related_id) <= 0
            or int(related_id) == memory_id
        ):
            return False

        if get_memory(int(related_id)) is None:
            return False

    existing_ids = []

    if memory["related_memory_ids"]:
        existing_ids = memory["related_memory_ids"].split(",")

    for related_id in new_ids:
        if related_id not in existing_ids:
            existing_ids.append(related_id)

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE memories
            SET related_memory_ids = ?
            WHERE id = ?
            """,
            (",".join(existing_ids), memory_id),
        )

    return ",".join(existing_ids)


def remember(
    category: str,
    content: str,
    previous_memory_id=None,
    related_memory_ids=None,
):
    """
    Store a new memory in the persistent database.

    Optional history and relationship references are validated before
    the memory is stored.

    Args:
        category: The memory category.
        content: The memory text.
        previous_memory_id: Optional ID of the previous version.
        related_memory_ids: Optional comma-separated related memory IDs.

    Returns:
        ``True`` when the memory is stored successfully, otherwise
        ``False`` when a supplied reference is invalid.
    """

    if previous_memory_id is not None:
        if previous_memory_id <= 0 or get_memory(previous_memory_id) is None:
            return False

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

        memory_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO memory_fts (rowid, content)
            VALUES (?, ?)
            """,
            (memory_id, content),
        )

    return True


def update_memory(memory_id: int, content: str):
    """
    Replace the content of an existing memory and update its search index.

    Args:
        memory_id: ID of the memory to update.
        content: The new memory text.

    Returns:
        ``True`` when the memory exists and is updated, otherwise
        ``False``.
    """

    memory = get_memory(memory_id)

    if memory is None:
        return False

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE memories
            SET content = ?
            WHERE id = ?
            """,
            (content, memory_id),
        )

        connection.execute(
            """
            INSERT INTO memory_fts(memory_fts, rowid, content)
            VALUES('delete', ?, ?)
            """,
            (memory_id, memory["content"]),
        )

        connection.execute(
            """
            INSERT INTO memory_fts(rowid, content)
            VALUES (?, ?)
            """,
            (memory_id, content),
        )

    return True


def get_memories(options=None):
    """
    Retrieve memories matching the supplied query options.

    Archived memories are excluded by default. Category filtering is
    applied when requested.

    Args:
        options: Optional memory query options. Defaults to
            ``get_memory_query_options()``.

    Returns:
        A list of memory dictionaries ordered by descending memory ID.
    """

    if options is None:
        options = get_memory_query_options()

    query = """
        SELECT id, created, category, status, content,
        previous_memory_id, related_memory_ids
        FROM memories
    """

    conditions = []
    parameters = []

    if not options["include_archived"]:
        conditions.append("status = 'active'")

    if options["category"]:
        conditions.append("category = ?")
        parameters.append(options["category"])

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY id DESC"

    with get_connection() as connection:
        rows = connection.execute(query, parameters).fetchall()

    return [
        {
            "id": row[0],
            "created": row[1],
            "category": row[2],
            "status": row[3],
            "content": row[4],
            "previous_memory_id": row[5],
            "related_memory_ids": row[6],
        }
        for row in rows
    ]


def search_memories(term, options=None):
    """
    Search memory content for a text term.

    Archived memories are excluded by default and the search can be
    restricted to a memory category.

    Args:
        term: Text to search for.
        options: Optional memory query options.

    Returns:
        A list of matching memory dictionaries.
    """

    if options is None:
        options = get_memory_query_options()

    query = """
        SELECT id, created, category, status, content,
        previous_memory_id, related_memory_ids
        FROM memories
        WHERE content LIKE ? ESCAPE '\\'
    """

    escaped_term = term.replace("\\", "\\\\")
    escaped_term = escaped_term.replace("%", "\\%")
    escaped_term = escaped_term.replace("_", "\\_")

    parameters = [f"%{escaped_term}%"]

    if not options["include_archived"]:
        query += " AND status = 'active'"

    if options["category"]:
        query += " AND category = ?"
        parameters.append(options["category"])

    query += " ORDER BY id"

    with get_connection() as connection:
        rows = connection.execute(query, parameters).fetchall()

    return [
        {
            "id": row[0],
            "created": row[1],
            "category": row[2],
            "status": row[3],
            "content": row[4],
            "previous_memory_id": row[5],
            "related_memory_ids": row[6],
        }
        for row in rows
    ]


def find_related_memory_candidates(content: str, limit=5):
    """
    Find existing memories that may be related to new memory content.

    Candidate memories are identified from shared significant terms.
    This is intended for interactive interfaces such as the TUI.
    It provides candidate memories only; it does not create relationships.

    Args:
        content: New memory content to compare with existing memories.
        limit: Maximum number of candidate memories to return.

    Returns:
        A list of candidate memory dictionaries, ordered by relevance.
    """

    words = [
        word
        for word in content.split()
        if len(word) >= 3
    ]

    if not words:
        return []

    terms = []

    for word in words:
        term = "".join(character for character in word if character.isalnum())

        if len(term) >= 3 and term not in terms:
            terms.append(term)

    if len(terms) < 2:
        return []


    with get_connection() as connection:
        matches = {}

        for term in terms:
            rows = connection.execute(
                """
                SELECT memories.id
                FROM memory_fts
                JOIN memories ON memories.id = memory_fts.rowid
                WHERE memory_fts MATCH ?
                  AND memories.status = 'active'
                """,
                (f'"{term}"',),
            ).fetchall()

            for row in rows:
                memory_id = row[0]
                matches[memory_id] = matches.get(memory_id, 0) + 1

        candidate_ids = [
            memory_id
            for memory_id, match_count in matches.items()
            if match_count >= 2
        ]

        candidate_ids.sort(
            key=lambda memory_id: matches[memory_id],
            reverse=True,
        )

        candidate_ids = candidate_ids[:limit]

        if not candidate_ids:
            return []

        placeholders = ",".join("?" for _ in candidate_ids)

        rows = connection.execute(
            f"""
            SELECT id, created, category, status, content,
                   previous_memory_id, related_memory_ids
            FROM memories
            WHERE id IN ({placeholders})
            ORDER BY id
            """,
            candidate_ids,
        ).fetchall()

    memories = {
        row[0]: {
            "id": row[0],
            "created": row[1],
            "category": row[2],
            "status": row[3],
            "content": row[4],
            "previous_memory_id": row[5],
            "related_memory_ids": row[6],
        }
        for row in rows
    }

    return [
        memories[memory_id]
        for memory_id in candidate_ids
        if memory_id in memories
    ]


def find_relevant_memories(question: str, limit=5):
    """
    Find active memories that may contain information relevant to a question.

    Candidate memories are identified from matching significant terms.
    This function provides possible evidence only; it does not determine
    whether a memory actually answers the question.

    Args:
        question: The user's question.
        limit: Maximum number of candidate memories to return.

    Returns:
        A list of candidate memory dictionaries, ordered by relevance.
    """

    stop_words = {
        "about",
        "after",
        "again",
        "also",
        "and",
        "are",
        "because",
        "been",
        "before",
        "being",
        "but",
        "can",
        "could",
        "does",
        "doing",
        "for",
        "from",
        "had",
        "has",
        "have",
        "how",
        "into",
        "its",
        "just",
        "more",
        "most",
        "not",
        "only",
        "our",
        "should",
        "some",
        "than",
        "that",
        "the",
        "their",
        "there",
        "these",
        "they",
        "this",
        "those",
        "through",
        "to",
        "was",
        "were",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "will",
        "with",
        "would",
        "you",
        "your",
    }

    terms = []

    for word in question.split():
        term = "".join(
            character
            for character in word
            if character.isalnum()
        ).lower()

        if (
            len(term) >= 3
            and term not in stop_words
            and term not in terms
        ):
            terms.append(term)

    if not terms:
        return []

    with get_connection() as connection:
        matches = {}

        for term in terms:
            rows = connection.execute(
                """
                SELECT memories.id
                FROM memory_fts
                JOIN memories ON memories.id = memory_fts.rowid
                WHERE memory_fts MATCH ?
                  AND memories.status = 'active'
                """,
                (f'"{term}"',),
            ).fetchall()

            for row in rows:
                memory_id = row[0]
                matches[memory_id] = matches.get(memory_id, 0) + 1

        candidate_ids = sorted(
            matches,
            key=lambda memory_id: (
                -matches[memory_id],
                memory_id,
            ),
        )[:limit]

        if not candidate_ids:
            return []

        placeholders = ",".join("?" for _ in candidate_ids)

        rows = connection.execute(
            f"""
            SELECT id, created, category, status, content,
                   previous_memory_id, related_memory_ids
            FROM memories
            WHERE id IN ({placeholders})
            ORDER BY id
            """,
            candidate_ids,
        ).fetchall()

    memories = {
        row[0]: {
            "id": row[0],
            "created": row[1],
            "category": row[2],
            "status": row[3],
            "content": row[4],
            "previous_memory_id": row[5],
            "related_memory_ids": row[6],
        }
        for row in rows
    }

    return [
        memories[memory_id]
        for memory_id in candidate_ids
        if memory_id in memories
    ]


def get_memory(memory_id: int):
    """
    Retrieve a single memory by ID.

    Args:
        memory_id: The ID of the memory to retrieve.

    Returns:
        The memory as a dictionary, or ``None`` if it does not exist.
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
    Retrieve the complete revision history for a memory.

    The returned history is ordered from the oldest version to the
    requested memory.

    Args:
        memory_id: ID of the memory whose history should be retrieved.

    Returns:
        A list of memory dictionaries in chronological order.
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


def archive_memories(memory_ids):
    """
    Archive multiple memories while preserving their identities.
    """

    archived = []
    missing = []

    for memory_id in memory_ids:
        if get_memory(memory_id) is None:
            missing.append(memory_id)
            continue

        archive_memory(memory_id)
        archived.append(memory_id)

    return {
        "archived": archived,
        "missing": missing,
    }


def restore_memory(memory_id: int):
    """
    Mark an archived memory as active.
    """

    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE memories
            SET status = 'active'
            WHERE id = ?
            """,
            (memory_id,),
        )


def restore_memories(memory_ids):
    """
    Restore multiple archived memories while preserving their identities.
    """

    restored = []
    missing = []

    for memory_id in memory_ids:
        if get_memory(memory_id) is None:
            missing.append(memory_id)
            continue

        restore_memory(memory_id)
        restored.append(memory_id)

    return {
        "restored": restored,
        "missing": missing,
    }


def delete_memory(memory_id: int):
    """
    Delete a memory permanently.
    """

    memory = get_memory(memory_id)

    if memory is None:
        return False

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO memory_fts(memory_fts, rowid, content)
            VALUES('delete', ?, ?)
            """,
            (memory_id, memory["content"]),
        )

        connection.execute(
            """
            DELETE FROM memories
            WHERE id = ?
            """,
            (memory_id,),
        )

    return True


def delete_memories(memory_ids):
    """
    Delete multiple memories while repairing their histories
    and relationships.
    """

    deleted = []
    missing = []

    for memory_id in memory_ids:
        if delete_memory(memory_id):
            deleted.append(memory_id)
        else:
            missing.append(memory_id)

    return {
        "deleted": deleted,
        "missing": missing,
    }


def get_memory_information():
    """
    Return information about ALF's memory system.
    """

    memories = get_memories()

    categories = []

    for memory in memories:
        category = memory["category"]

        if category not in categories:
            categories.append(category)

    return {
        "total_memories": len(memories),
        "categories": categories,
    }


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
