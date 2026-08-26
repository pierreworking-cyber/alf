import pytest

from alf import memory


@pytest.fixture
def database(tmp_path, monkeypatch):
    database = tmp_path / "alf.db"
    monkeypatch.setattr(memory, "DATABASE", database)
    return database


def test_database_is_created(database):
    with memory.get_connection() as connection:
        tables = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'memories'"
        ).fetchall()

    assert tables == [("memories",)]


def test_memory_fts_is_created(database):
    with memory.get_connection() as connection:
        tables = connection.execute(
            "SELECT name FROM sqlite_master WHERE name = 'memory_fts'"
        ).fetchall()

    assert tables == [("memory_fts",)]


def test_database_migrates_schema_from_version_one(database):
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
        ("2026-01-01 12:00:00", "note", "Existing Austerlitz memory."),
    )

    connection.execute("PRAGMA user_version = 1")
    connection.commit()
    connection.close()

    with memory.get_connection() as connection:
        version = connection.execute(
            "PRAGMA user_version"
        ).fetchone()[0]

        results = connection.execute(
            """
            SELECT rowid
            FROM memory_fts
            WHERE memory_fts MATCH ?
            """,
            ("Austerlitz",),
        ).fetchall()

        mindmap_tables = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name IN ('mindmaps', 'mindmap_documents')
            ORDER BY name
            """
        ).fetchall()

    assert version == 5
    assert results == [(1,)]
    assert mindmap_tables == [
        ("mindmap_documents",),
        ("mindmaps",),
    ]


def test_database_migrates_mindmaps_from_version_four(database):
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
        CREATE TABLE mindmaps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            project TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created TEXT NOT NULL,
            modified TEXT NOT NULL
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE mindmap_documents (
            mindmap_id INTEGER PRIMARY KEY,
            content TEXT NOT NULL,
            FOREIGN KEY (mindmap_id)
                REFERENCES mindmaps(id)
                ON DELETE CASCADE
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE mindmap_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL DEFAULT 'active',
            created TEXT NOT NULL,
            modified TEXT NOT NULL
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE mindmap_projects (
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

    connection.execute(
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
            "Uncategorised",
            "Garden",
            "active",
            "2026-08-25 10:00:00",
            "2026-08-25 11:00:00",
        ),
    )

    mindmap_id = connection.execute(
        "SELECT last_insert_rowid()"
    ).fetchone()[0]

    connection.execute(
        """
        INSERT INTO mindmap_documents (
            mindmap_id,
            content
        )
        VALUES (?, ?)
        """,
        (
            mindmap_id,
            '{"meta":{"name":"Garden"},"format":"node_array","data":[]}',
        ),
    )

    connection.execute("PRAGMA user_version = 4")
    connection.commit()
    connection.close()

    with memory.get_connection() as connection:
        version = connection.execute(
            "PRAGMA user_version"
        ).fetchone()[0]

        category = connection.execute(
            """
            SELECT id, name
            FROM mindmap_categories
            WHERE name = ?
            """,
            ("Uncategorised",),
        ).fetchone()

        mindmap = connection.execute(
            """
            SELECT category_id, name
            FROM mindmaps
            WHERE id = ?
            """,
            (mindmap_id,),
        ).fetchone()

        document = connection.execute(
            """
            SELECT content
            FROM mindmap_documents
            WHERE mindmap_id = ?
            """,
            (mindmap_id,),
        ).fetchone()

    assert version == 5
    assert category is not None
    assert mindmap[0] == category[0]
    assert mindmap[1] == "Garden"
    assert document[0] == (
        '{"meta":{"name":"Garden"},"format":"node_array","data":[]}'
    )


def test_database_schema_version(database):
    with memory.get_connection() as connection:
        version = connection.execute("PRAGMA user_version").fetchone()[0]

    assert version == memory.SCHEMA_VERSION


def test_create_mindmap_category(database):
    category_id = memory.create_mindmap_category("House")

    assert category_id == 1

    with memory.get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, name, status
            FROM mindmap_categories
            WHERE id = ?
            """,
            (category_id,),
        ).fetchone()

    assert row[0] == 1
    assert row[1] == "House"
    assert row[2] == "active"


def test_get_mindmap_categories(database):
    memory.create_mindmap_category("House")
    memory.create_mindmap_category("Events")

    categories = memory.get_mindmap_categories()

    assert [category["name"] for category in categories] == [
        "House",
        "Events",
    ]


def test_get_mindmap_categories_returns_empty_list(database):
    assert memory.get_mindmap_categories() == []


def test_update_mindmap_category(database):
    memory.create_mindmap_category("House")

    result = memory.update_mindmap_category(
        1,
        name="Home",
        status="archived",
    )

    assert result is True

    category = memory.get_mindmap_categories()[0]

    assert category["name"] == "Home"
    assert category["status"] == "archived"


def test_update_missing_mindmap_category(database):
    result = memory.update_mindmap_category(
        999,
        name="Missing category",
        status="active",
    )

    assert result is False


def test_archive_mindmap_category(database):
    memory.create_mindmap_category("House")

    result = memory.archive_mindmap_category(1)

    assert result is True
    assert memory.get_mindmap_categories()[0]["status"] == "archived"


def test_archive_missing_mindmap_category(database):
    assert memory.archive_mindmap_category(999) is False


def test_delete_mindmap_category(database):
    memory.create_mindmap_category("House")

    result = memory.delete_mindmap_category(1)

    assert result is True
    assert memory.get_mindmap_categories() == []


def test_delete_missing_mindmap_category(database):
    assert memory.delete_mindmap_category(999) is False


def test_delete_mindmap_category_deletes_maps(database):
    category_id = memory.create_mindmap_category("Birthday")
    mindmap_id = memory.create_mindmap(
        "Birthday",
        "Party plan",
        '{"meta":{"name":"Party plan"},"format":"node_array","data":[]}',
    )

    result = memory.delete_mindmap_category(category_id)

    assert result is True
    assert memory.get_mindmaps() == []
    assert memory.get_mindmap(mindmap_id) is None


def test_connection_persists_data(database):
    with memory.get_connection() as connection:
        connection.execute(
            """
            INSERT INTO memories (created, category, content)
            VALUES (?, ?, ?)
            """,
            ("2026-01-01 12:00:00", "note", "Persistent test."),
        )

    with memory.get_connection() as connection:
        row = connection.execute("SELECT content FROM memories WHERE id = 1").fetchone()

    assert row == ("Persistent test.",)


def test_create_mindmap(database):
    mindmap_id = memory.create_mindmap(
        "House",
        "Living room redecorate",
        "<map><node>Living room</node></map>",
    )

    assert mindmap_id == 1


def test_get_mindmaps(database):
    memory.create_mindmap(
        "House",
        "Living room redecorate",
        "<map><node>Living room</node></map>",
    )
    memory.create_mindmap(
        "Events",
        "Sue birthday",
        "<map><node>Sue birthday</node></map>",
    )

    mindmaps = memory.get_mindmaps()

    assert [item["id"] for item in mindmaps] == [1, 2]
    assert [item["category"] for item in mindmaps] == ["House", "Events"]
    assert [item["name"] for item in mindmaps] == [
        "Living room redecorate",
        "Sue birthday",
    ]


def test_get_mindmaps_returns_empty_list(database):
    assert memory.get_mindmaps() == []


def test_update_mindmap(database):
    memory.create_mindmap(
        "House",
        "Living room redecorate",
        "<map><node>Living room</node></map>",
    )

    result = memory.update_mindmap(
        1,
        category="House",
        name="Living room finished",
        status="active",
        content="<map><node>Finished living room</node></map>",
    )

    assert result is True

    mindmap = memory.get_mindmap(1)

    assert mindmap["category"] == "House"
    assert mindmap["name"] == "Living room finished"
    assert mindmap["status"] == "active"
    assert mindmap["content"] == "<map><node>Finished living room</node></map>"


def test_update_missing_mindmap(database):
    result = memory.update_mindmap(
        999,
        category="House",
        name="Missing map",
        status="active",
        content="<map><node>Missing</node></map>",
    )

    assert result is False


def test_archive_mindmap(database):
    memory.create_mindmap(
        "House",
        "Living room redecorate",
        "<map><node>Living room</node></map>",
    )

    result = memory.archive_mindmap(1)

    assert result is True
    assert memory.get_mindmap(1)["status"] == "archived"


def test_delete_mindmap(database):
    memory.create_mindmap(
        "House",
        "Living room redecorate",
        "<map><node>Living room</node></map>",
    )

    result = memory.delete_mindmap(1)

    assert result is True
    assert memory.get_mindmap(1) is None

    with memory.get_connection() as connection:
        document = connection.execute(
            """
            SELECT mindmap_id
            FROM mindmap_documents
            WHERE mindmap_id = 1
            """
        ).fetchone()

    assert document is None


def test_delete_missing_mindmap(database):
    assert memory.delete_mindmap(999) is False


def test_archive_missing_mindmap(database):
    assert memory.archive_mindmap(999) is False


def test_get_memory_categories():
    categories = memory.get_memory_categories()

    assert categories == [
        "note",
        "fact",
        "decision",
        "preference",
    ]


def test_default_memory_query_options():
    assert memory.get_memory_query_options() == {
        "category": None,
        "include_archived": False,
        "group": None,
    }


def test_validate_related_memory_ids_with_no_ids(database):
    assert memory.validate_related_memory_ids(None) is None


def test_validate_related_memory_ids_with_valid_ids(database):
    memory.remember("note", "First memory.")
    memory.remember("note", "Second memory.")

    assert memory.validate_related_memory_ids("1,2") == "1,2"


def test_remember_stores_previous_memory(database):
    memory.remember("note", "Original memory.")
    memory.remember(
        "note",
        "Updated memory.",
        previous_memory_id=1,
    )

    result = memory.get_memory(2)

    assert result["previous_memory_id"] == 1


def test_remember_rejects_invalid_previous_memory(database):
    result = memory.remember(
        "note",
        "Invalid history link.",
        previous_memory_id=999,
    )

    assert result is False
    assert memory.get_memories() == []


def test_update_memory_changes_content_without_creating_memory(database):
    memory.remember("note", "Original memory.")

    result = memory.update_memory(1, "Edited memory.")

    assert result is True
    assert memory.get_memory(1)["content"] == "Edited memory."
    assert memory.get_memories() == [
        {
            "id": 1,
            "created": memory.get_memory(1)["created"],
            "category": "note",
            "status": "active",
            "content": "Edited memory.",
            "previous_memory_id": None,
            "related_memory_ids": None,
        }
    ]


def test_update_memory_updates_fts_index(database):
    memory.remember("note", "Original memory.")

    memory.update_memory(1, "Edited memory.")

    with memory.get_connection() as connection:
        old_results = connection.execute(
            """
            SELECT rowid
            FROM memory_fts
            WHERE memory_fts MATCH ?
            """,
            ("Original",),
        ).fetchall()

        new_results = connection.execute(
            """
            SELECT rowid
            FROM memory_fts
            WHERE memory_fts MATCH ?
            """,
            ("Edited",),
        ).fetchall()

    assert old_results == []
    assert new_results == [(1,)]


def test_remember_rejects_invalid_related_memory(database):
    result = memory.remember(
        "note",
        "Invalid relationship.",
        related_memory_ids="999",
    )

    assert result is False
    assert memory.get_memories() == []


def test_validate_related_memory_ids_rejects_invalid_id(database):
    assert memory.validate_related_memory_ids("abc") is False
    assert memory.validate_related_memory_ids("0") is False
    assert memory.validate_related_memory_ids("-1") is False


def test_relate_memory_adds_relationship(database):
    memory.remember("note", "First memory.")
    memory.remember("note", "Second memory.")
    memory.remember("note", "Third memory.")

    result = memory.relate_memory(3, "1,2")

    assert result == "1,2"
    assert memory.get_memory(3)["related_memory_ids"] == "1,2"


def test_relate_memory_preserves_existing_relationships(database):
    memory.remember("note", "First memory.")
    memory.remember("note", "Second memory.")
    memory.remember(
        "note",
        "Third memory.",
        related_memory_ids="1",
    )

    result = memory.relate_memory(3, "2")

    assert result == "1,2"
    assert memory.get_memory(3)["related_memory_ids"] == "1,2"


def test_relate_memory_ignores_duplicate_relationships(database):
    memory.remember("note", "First memory.")
    memory.remember("note", "Second memory.")

    memory.remember(
        "note",
        "Third memory.",
        related_memory_ids="1",
    )

    result = memory.relate_memory(3, "1")

    assert result == "1"
    assert memory.get_memory(3)["related_memory_ids"] == "1"


def test_relate_memory_rejects_missing_source(database):
    memory.remember("note", "Existing memory.")

    assert memory.relate_memory(999, "1") is False


def test_relate_memory_rejects_missing_target(database):
    memory.remember("note", "Existing memory.")

    assert memory.relate_memory(1, "999") is False


def test_relate_memory_rejects_self_relationship(database):
    memory.remember("note", "Existing memory.")

    assert memory.relate_memory(1, "1") is False


def test_validate_related_memory_ids_requires_existing_memory(database):
    memory.remember("note", "Existing memory.")

    assert memory.validate_related_memory_ids("1,999") is False


def test_memory_categories_match_defined_categories():
    assert memory.get_memory_categories() == memory.VALID_MEMORY_CATEGORIES


def test_categories_are_returned_as_a_copy():
    categories = memory.get_memory_categories()
    categories.append("temporary")

    assert "temporary" not in memory.get_memory_categories()


def test_remember_and_get_memory(database):
    assert memory.remember("note", "This is a test memory.") is True

    result = memory.get_memory(1)

    assert result["id"] == 1
    assert result["category"] == "note"
    assert result["content"] == "This is a test memory."
    assert result["status"] == "active"


def test_remember_indexes_memory_for_fts_search(database):
    memory.remember("note", "The Battle of Austerlitz.")

    with memory.get_connection() as connection:
        results = connection.execute(
            """
            SELECT rowid
            FROM memory_fts
            WHERE memory_fts MATCH ?
            """,
            ("Austerlitz",),
        ).fetchall()

    assert results == [(1,)]


def test_get_memories(database):
    memory.remember("note", "First memory.")
    memory.remember("fact", "Second memory.")

    memories = memory.get_memories()

    assert len(memories) == 2
    assert memories[0]["content"] == "Second memory."
    assert memories[1]["content"] == "First memory."


def test_get_memories_by_category(database):
    memory.remember("note", "A note.")
    memory.remember("fact", "A fact.")

    memories = memory.get_memories(
        {"category": "note", "include_archived": False, "group": None}
    )

    assert len(memories) == 1
    assert memories[0]["content"] == "A note."


def test_get_memories_includes_archived_when_requested(database):
    memory.remember("note", "Active memory.")
    memory.remember("note", "Archived memory.")

    memory.archive_memory(2)

    memories = memory.get_memories()

    assert [item["id"] for item in memories] == [1]

    memories = memory.get_memories(
        {"category": None, "include_archived": True, "group": None}
    )

    assert [item["id"] for item in memories] == [2, 1]


def test_get_memories_returns_newest_first(database):
    memory.remember("note", "First memory.")
    memory.remember("note", "Second memory.")
    memory.remember("note", "Third memory.")

    memories = memory.get_memories()

    assert [item["id"] for item in memories] == [3, 2, 1]


def test_get_memories_does_not_modify_options(database):
    options = memory.get_memory_query_options()

    memory.remember("note", "Test memory.")
    memory.get_memories(options)

    assert options == {
        "category": None,
        "include_archived": False,
        "group": None,
    }


def test_get_memory_returns_memory_by_id(database):
    memory.remember("note", "A specific memory.")

    result = memory.get_memory(1)

    assert result == {
        "id": 1,
        "created": result["created"],
        "category": "note",
        "status": "active",
        "content": "A specific memory.",
        "previous_memory_id": None,
        "related_memory_ids": None,
    }


def test_get_memory_returns_relationships(database):
    memory.remember("note", "Original memory.")
    memory.remember(
        "note",
        "Related memory.",
        related_memory_ids="1",
    )
    memory.remember(
        "note",
        "Revised memory.",
        previous_memory_id=2,
    )

    result = memory.get_memory(3)

    assert result["previous_memory_id"] == 2
    assert result["related_memory_ids"] is None

    result = memory.get_memory(2)

    assert result["previous_memory_id"] is None
    assert result["related_memory_ids"] == "1"


def test_get_related_memories_returns_empty_without_relationships(database):
    memory.remember("note", "Standalone memory.")

    assert memory.get_related_memories(1) == []


def test_memory_information_is_empty_when_no_memories_exist(database):
    information = memory.get_memory_information()

    assert information == {
        "total_memories": 0,
        "categories": [],
    }


def test_get_related_memories_returns_direct_relationships(database):
    memory.remember("note", "First memory.")
    memory.remember("note", "Second memory.")
    memory.remember(
        "note",
        "Third memory.",
        related_memory_ids="1,2",
    )

    related = memory.get_related_memories(3)

    assert [item["id"] for item in related] == [1, 2]


def test_get_related_memories_ignores_missing_related_memory(database):
    memory.remember("note", "Existing memory.")
    memory.remember("note", "Memory with invalid relationship.")

    with memory.get_connection() as connection:
        connection.execute(
            """
            UPDATE memories
            SET related_memory_ids = ?
            WHERE id = ?
            """,
            ("999", 2),
        )

    related = memory.get_related_memories(2)

    assert related == []


def test_get_memory_history_returns_single_memory(database):
    memory.remember("note", "First memory.")

    history = memory.get_memory_history(1)

    assert [item["id"] for item in history] == [1]


def test_get_memory_history_returns_chain_oldest_first(database):
    memory.remember("note", "First memory.")
    memory.remember(
        "note",
        "Second memory.",
        previous_memory_id=1,
    )
    memory.remember(
        "note",
        "Third memory.",
        previous_memory_id=2,
    )

    history = memory.get_memory_history(3)

    assert [item["id"] for item in history] == [1, 2, 3]


def test_get_memory_history_returns_empty_for_missing_memory(database):
    assert memory.get_memory_history(999) == []


def test_get_memory_history_stops_at_missing_previous_memory(database):
    memory.remember("note", "Original.")
    memory.remember(
        "note",
        "Revision.",
        previous_memory_id=1,
    )

    with memory.get_connection() as connection:
        connection.execute(
            """
            UPDATE memories
            SET previous_memory_id = ?
            WHERE id = ?
            """,
            (999, 2),
        )

    history = memory.get_memory_history(2)

    assert [item["id"] for item in history] == [2]


def test_get_related_memories_does_not_follow_relationships(database):
    memory.remember("note", "First memory.")
    memory.remember(
        "note",
        "Second memory.",
        related_memory_ids="1",
    )
    memory.remember(
        "note",
        "Third memory.",
        related_memory_ids="2",
    )

    related = memory.get_related_memories(3)

    assert [item["id"] for item in related] == [2]


def test_get_memory_returns_none_for_missing_id(database):
    assert memory.get_memory(999) is None


def test_search_memories_finds_matching_content(database):
    memory.remember("note", "The moon looks larger near the horizon.")
    memory.remember("note", "The sky is blue.")

    results = memory.search_memories("moon")

    assert len(results) == 1
    assert results[0]["content"] == "The moon looks larger near the horizon."


def test_search_memories_treats_percent_as_literal(database):
    memory.remember("note", "The completion rate is 100%.")
    memory.remember("note", "The completion rate is 100 percent.")

    results = memory.search_memories("100%")

    assert [item["content"] for item in results] == [
        "The completion rate is 100%."
    ]


def test_search_memories_treats_underscore_as_literal(database):
    memory.remember("note", "Use ALF_DEBUG_MODE when debugging.")
    memory.remember("note", "Use ALF debug mode when debugging.")

    results = memory.search_memories("ALF_DEBUG")

    assert [item["content"] for item in results] == [
        "Use ALF_DEBUG_MODE when debugging."
    ]


def test_search_memories_respects_category_and_archive_options(database):
    memory.remember("note", "Active note about ALF.")
    memory.remember("fact", "Active fact about ALF.")
    memory.remember("note", "Archived note about ALF.")

    memory.archive_memory(3)

    results = memory.search_memories(
        "ALF",
        {
            "category": "note",
            "include_archived": False,
            "group": None,
        },
    )

    assert [item["id"] for item in results] == [1]

    results = memory.search_memories(
        "ALF",
        {
            "category": "note",
            "include_archived": True,
            "group": None,
        },
    )

    assert [item["id"] for item in results] == [1, 3]


def test_search_memories_returns_empty_for_no_match(database):
    memory.remember("note", "The moon is interesting.")

    results = memory.search_memories("banana")

    assert results == []


def test_find_related_memory_candidates_finds_matching_memories(database):
    memory.remember(
        "note",
        "ALF should remain a simple and useful computing companion.",
    )
    memory.remember(
        "note",
        "SQLite provides persistent storage for ALF memory.",
    )
    memory.remember(
        "note",
        "The garden needs watering this evening.",
    )

    results = memory.find_related_memory_candidates(
        "ALF computing companion"
    )

    assert len(results) == 1
    assert results[0]["content"] == (
        "ALF should remain a simple and useful computing companion."
    )


def test_find_related_memory_candidates_is_case_insensitive(database):
    memory.remember(
        "note",
        "ALF should remain a simple and useful computing companion.",
    )

    results = memory.find_related_memory_candidates(
        "alf computing companion"
    )

    assert len(results) == 1
    assert results[0]["content"] == (
        "ALF should remain a simple and useful computing companion."
    )


def test_find_related_memory_candidates_requires_multiple_matching_terms(
    database,
):
    memory.remember(
        "note",
        "ALF should remain a simple and useful computing companion.",
    )
    memory.remember(
        "note",
        "SQLite provides persistent storage for ALF memory.",
    )

    results = memory.find_related_memory_candidates(
        "ALF computing companion"
    )

    assert [item["id"] for item in results] == [1]


def test_find_related_memory_candidates_limits_results(database):
    for index in range(6):
        memory.remember(
            "note",
            f"ALF memory about computing companion {index}.",
        )

    results = memory.find_related_memory_candidates(
        "ALF computing companion"
    )

    assert len(results) == 5


def test_find_related_memory_candidates_ignores_archived_memories(database):
    memory.remember(
        "note",
        "ALF should remain a useful computing companion.",
    )
    memory.remember(
        "note",
        "An archived ALF computing companion memory.",
    )

    memory.archive_memory(2)

    results = memory.find_related_memory_candidates(
        "ALF computing companion"
    )

    assert [item["id"] for item in results] == [1]


def test_find_related_memory_candidates_ignores_short_input(database):
    memory.remember(
        "note",
        "ALF should remain a useful computing companion.",
    )

    assert memory.find_related_memory_candidates("Al") == []


def test_find_relevant_memories_finds_matching_memory(database):
    memory.remember(
        "preference",
        "Peter prefers Neovim for Python programming.",
    )
    memory.remember(
        "note",
        "The garden needs watering this evening.",
    )

    results = memory.find_relevant_memories(
        "What editor does Peter prefer for Python programming?"
    )

    assert len(results) == 1
    assert results[0]["content"] == (
        "Peter prefers Neovim for Python programming."
    )


def test_find_relevant_memories_allows_single_matching_term(database):
    memory.remember(
        "note",
        "Peter uses Neovim every day.",
    )
    memory.remember(
        "note",
        "The garden needs watering.",
    )

    results = memory.find_relevant_memories(
        "What is Neovim?"
    )

    assert [item["id"] for item in results] == [1]


def test_find_relevant_memories_returns_empty_for_only_stop_words(
    database,
):
    memory.remember(
        "note",
        "The garden needs watering.",
    )

    results = memory.find_relevant_memories(
        "What is the?"
    )

    assert results == []


def test_find_relevant_memories_is_case_insensitive(database):
    memory.remember(
        "note",
        "Peter prefers Neovim for Python programming.",
    )

    results = memory.find_relevant_memories(
        "PYTHON PROGRAMMING"
    )

    assert len(results) == 1
    assert results[0]["id"] == 1


def test_find_relevant_memories_ignores_archived_memories(database):
    memory.remember(
        "note",
        "Peter prefers Neovim for Python programming.",
    )

    memory.archive_memory(1)

    results = memory.find_relevant_memories(
        "What editor does Peter prefer?"
    )

    assert results == []


def test_find_relevant_memories_limits_results(database):
    for index in range(6):
        memory.remember(
            "note",
            f"Python programming memory {index}.",
        )

    results = memory.find_relevant_memories(
        "Tell me about Python programming."
    )

    assert len(results) == 5


def test_find_relevant_memories_ranks_by_matching_terms(database):
    memory.remember(
        "note",
        "Python is useful.",
    )
    memory.remember(
        "note",
        "Python programming is useful.",
    )
    memory.remember(
        "note",
        "Python programming with Neovim is useful.",
    )

    results = memory.find_relevant_memories(
        "Tell me about Python programming with Neovim."
    )

    assert [item["id"] for item in results] == [3, 2, 1]


def test_archive_memory(database):
    memory.remember("note", "Archive me.")

    memory.archive_memory(1)

    assert memory.get_memories() == []

    memories = memory.get_memories(
        {"category": None, "include_archived": True, "group": None}
    )

    assert memories[0]["status"] == "archived"


def test_archive_memory_archives_memory(database):
    memory.remember("note", "Memory to archive.")

    memory.archive_memory(1)

    result = memory.get_memory(1)

    assert result["status"] == "archived"
    assert result["content"] == "Memory to archive."


def test_archive_memory_does_not_change_content(database):
    memory.remember("fact", "Important fact.")

    memory.archive_memory(1)

    result = memory.get_memory(1)

    assert result["content"] == "Important fact."


def test_archive_memory_handles_missing_memory(database):
    memory.archive_memory(999)

    assert memory.get_memory(999) is None


def test_archive_memories_archives_multiple_memories(database):
    memory.remember("note", "First memory.")
    memory.remember("note", "Second memory.")
    memory.remember("note", "Third memory.")

    result = memory.archive_memories([1, 2, 3])

    assert result == {
        "archived": [1, 2, 3],
        "missing": [],
    }

    assert memory.get_memory(1)["status"] == "archived"
    assert memory.get_memory(2)["status"] == "archived"
    assert memory.get_memory(3)["status"] == "archived"


def test_archive_memories_preserves_content(database):
    memory.remember("note", "First memory.")
    memory.remember("note", "Second memory.")

    memory.archive_memories([1, 2])

    assert memory.get_memory(1)["content"] == "First memory."
    assert memory.get_memory(2)["content"] == "Second memory."


def test_archive_memories_reports_missing_ids(database):
    memory.remember("note", "First memory.")
    memory.remember("note", "Second memory.")

    result = memory.archive_memories([1, 999, 2])

    assert result == {
        "archived": [1, 2],
        "missing": [999],
    }


def test_restore_memories_restores_archived_memories(database):
    memory.remember("note", "First memory.")
    memory.remember("note", "Second memory.")

    memory.archive_memories([1, 2])

    result = memory.restore_memories([1, 2])

    assert result == {
        "restored": [1, 2],
        "missing": [],
    }

    assert memory.get_memory(1)["status"] == "active"
    assert memory.get_memory(2)["status"] == "active"


def test_restore_memories_reports_missing_ids(database):
    memory.remember("note", "First memory.")

    result = memory.restore_memories([1, 999])

    assert result == {
        "restored": [1],
        "missing": [999],
    }


def test_delete_memory_removes_memory(database):
    memory.remember("note", "Delete me.")

    assert memory.delete_memory(1) is True

    assert memory.get_memory(1) is None


def test_delete_memory_removes_memory_from_fts(database):
    memory.remember("note", "Memory to delete.")

    memory.delete_memory(1)

    with memory.get_connection() as connection:
        results = connection.execute(
            """
            SELECT rowid
            FROM memory_fts
            WHERE memory_fts MATCH ?
            """,
            ("delete",),
        ).fetchall()

    assert results == []


def test_delete_memory_preserves_other_memories(database):
    memory.remember("note", "First memory.")
    memory.remember("note", "Second memory.")
    memory.remember("note", "Third memory.")

    memory.delete_memory(2)

    assert memory.get_memory(1)["content"] == "First memory."
    assert memory.get_memory(3)["content"] == "Third memory."


def test_delete_memory_leaves_history_reference_to_deleted_memory(database):
    memory.remember("note", "Original.")
    memory.remember(
        "note",
        "Revision.",
        previous_memory_id=1,
    )
    memory.remember(
        "note",
        "Final revision.",
        previous_memory_id=2,
    )

    memory.delete_memory(2)

    result = memory.get_memory(3)

    assert result["previous_memory_id"] == 2

    history = memory.get_memory_history(3)

    assert [item["id"] for item in history] == [3]


def test_delete_memory_leaves_history_reference_when_first_memory_is_deleted(
    database,
):
    memory.remember("note", "Original.")
    memory.remember(
        "note",
        "Revision.",
        previous_memory_id=1,
    )

    memory.delete_memory(1)

    result = memory.get_memory(2)

    assert result["previous_memory_id"] == 1

    history = memory.get_memory_history(2)

    assert [item["id"] for item in history] == [2]


def test_delete_memory_leaves_related_memory_id(database):
    memory.remember("note", "First memory.")
    memory.remember(
        "note",
        "Second memory.",
        related_memory_ids="1",
    )

    memory.delete_memory(1)

    result = memory.get_memory(2)

    assert result["related_memory_ids"] == "1"
    assert memory.get_related_memories(2) == []


def test_delete_memory_leaves_multiple_related_memory_ids(database):
    memory.remember("note", "First memory.")
    memory.remember("note", "Second memory.")
    memory.remember(
        "note",
        "Third memory.",
        related_memory_ids="1,2",
    )

    memory.delete_memory(1)

    result = memory.get_memory(3)

    assert result["related_memory_ids"] == "1,2"
    assert [item["id"] for item in memory.get_related_memories(3)] == [2]


def test_delete_memory_leaves_history_and_relationship_references(database):
    memory.remember("note", "Original.")
    memory.remember(
        "note",
        "Revision.",
        previous_memory_id=1,
    )
    memory.remember(
        "note",
        "Related memory.",
        related_memory_ids="2",
    )

    memory.delete_memory(2)

    result = memory.get_memory(3)

    assert result["previous_memory_id"] is None
    assert result["related_memory_ids"] == "2"
    assert memory.get_related_memories(3) == []


def test_delete_memory_handles_missing_memory(database):
    assert memory.delete_memory(999) is False


def test_delete_memories_deletes_multiple_memories(database):
    memory.remember("note", "First memory.")
    memory.remember("note", "Second memory.")
    memory.remember("note", "Third memory.")

    result = memory.delete_memories([1, 2, 3])

    assert result == {
        "deleted": [1, 2, 3],
        "missing": [],
    }

    assert memory.get_memory(1) is None
    assert memory.get_memory(2) is None
    assert memory.get_memory(3) is None


def test_delete_memories_reports_missing_ids(database):
    memory.remember("note", "First memory.")
    memory.remember("note", "Second memory.")

    result = memory.delete_memories([1, 999, 2])

    assert result == {
        "deleted": [1, 2],
        "missing": [999],
    }

    assert memory.get_memory(1) is None
    assert memory.get_memory(2) is None


def test_search_memories(database):
    memory.remember("note", "The moon is interesting.")
    memory.remember("fact", "The Earth has one moon.")

    results = memory.search_memories("moon")

    assert len(results) == 2


def test_related_memories(database):
    memory.remember("note", "First memory.")
    memory.remember("note", "Second memory.")

    memory.remember(
        "note",
        "Third memory.",
        related_memory_ids="1,2",
    )

    related = memory.get_related_memories(3)

    assert [item["id"] for item in related] == [1, 2]


def test_invalid_related_memory(database):
    assert memory.validate_related_memory_ids("999") is False


def test_memory_history(database):
    memory.remember("note", "Original.")
    memory.remember(
        "note",
        "Revision.",
        previous_memory_id=1,
    )
    memory.remember(
        "note",
        "Final revision.",
        previous_memory_id=2,
    )

    history = memory.get_memory_history(3)

    assert [item["id"] for item in history] == [1, 2, 3]


def test_memory_information(database):
    memory.remember("note", "A note.")
    memory.remember("fact", "A fact.")

    information = memory.get_memory_information()

    assert information["total_memories"] == 2
    assert information["categories"] == ["fact", "note"]


def test_capability(database):
    capability = memory.get_capability()

    assert capability["id"] == "memory"
    assert capability["name"] == "Persistent memory"
    assert capability["description"] == "SQLite-backed memory storage"
    assert capability["details"] == {
        "total_memories": 0,
        "categories": [],
    }
