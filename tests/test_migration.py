from alf import memory


def test_database_initialises_schema_version_one(database):
    with memory.get_connection() as connection:
        version = connection.execute(
            "PRAGMA user_version"
        ).fetchone()[0]

        tables = {
            row[0]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """
            ).fetchall()
        }

        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(memories)"
            ).fetchall()
        }

    assert version == 1
    assert "memories" in tables
    assert "memory_categories" in tables
    assert "memory_fts" in tables
    assert "memory_category_id" in columns


def test_database_migrates_legacy_memories_to_version_one(database):
    connection = memory.sqlite3.connect(database)

    connection.execute(
        """
        CREATE TABLE memories (
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

    connection.execute(
        """
        INSERT INTO memories (created, category, content)
        VALUES (?, ?, ?)
        """,
        (
            "2026-09-01 12:00:00",
            "note",
            "Existing Austerlitz memory.",
        ),
    )

    connection.commit()
    connection.close()

    with memory.get_connection() as connection:
        version = connection.execute(
            "PRAGMA user_version"
        ).fetchone()[0]

        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(memories)"
            ).fetchall()
        }

        memory_row = connection.execute(
            """
            SELECT content, memory_category_id
            FROM memories
            WHERE id = 1
            """
        ).fetchone()

        results = connection.execute(
            """
            SELECT rowid
            FROM memory_fts
            WHERE memory_fts MATCH ?
            """,
            ("Austerlitz",),
        ).fetchall()

    assert version == 1
    assert "memory_category_id" in columns
    assert memory_row == (
        "Existing Austerlitz memory.",
        None,
    )
    assert results == [(1,)]


def test_database_schema_version_matches_constant(database):
    with memory.get_connection() as connection:
        version = connection.execute(
            "PRAGMA user_version"
        ).fetchone()[0]

    assert version == memory.SCHEMA_VERSION
