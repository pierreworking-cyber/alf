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


def test_database_schema_version(database):
    with memory.get_connection() as connection:
        version = connection.execute("PRAGMA user_version").fetchone()[0]

    assert version == memory.SCHEMA_VERSION


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


def test_get_memories(database):
    memory.remember("note", "First memory.")
    memory.remember("fact", "Second memory.")

    memories = memory.get_memories()

    assert len(memories) == 2
    assert memories[0]["content"] == "First memory."
    assert memories[1]["content"] == "Second memory."


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

    assert [item["id"] for item in memories] == [1, 2]


def test_get_memories_returns_id_order(database):
    memory.remember("note", "First memory.")
    memory.remember("note", "Second memory.")
    memory.remember("note", "Third memory.")

    memories = memory.get_memories()

    assert [item["id"] for item in memories] == [1, 2, 3]


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


def test_forget_memory(database):
    memory.remember("note", "Forget me.")

    memory.forget_memory(1)

    result = memory.get_memory(1)

    assert result["status"] == "forgotten"
    assert result["content"] == "[forgotten]"


def test_forget_memory_marks_memory_forgotten(database):
    memory.remember("note", "Memory to forget.")

    memory.forget_memory(1)

    result = memory.get_memory(1)

    assert result["status"] == "forgotten"
    assert result["content"] == "[forgotten]"


def test_forget_memory_preserves_memory_id(database):
    memory.remember("note", "Memory to forget.")

    memory.forget_memory(1)

    result = memory.get_memory(1)

    assert result["id"] == 1


def test_forget_memory_handles_missing_memory(database):
    memory.forget_memory(999)

    assert memory.get_memory(999) is None


def test_forget_memories_forgets_multiple_memories(database):
    memory.remember("note", "First memory.")
    memory.remember("note", "Second memory.")
    memory.remember("note", "Third memory.")

    result = memory.forget_memories([1, 2, 3])

    assert result == {
        "forgotten": [1, 2, 3],
        "missing": [],
    }

    assert memory.get_memory(1)["status"] == "forgotten"
    assert memory.get_memory(2)["status"] == "forgotten"
    assert memory.get_memory(3)["status"] == "forgotten"


def test_forget_memories_replaces_content(database):
    memory.remember("note", "First memory.")
    memory.remember("note", "Second memory.")

    memory.forget_memories([1, 2])

    assert memory.get_memory(1)["content"] == "[forgotten]"
    assert memory.get_memory(2)["content"] == "[forgotten]"


def test_forget_memories_reports_missing_ids(database):
    memory.remember("note", "First memory.")
    memory.remember("note", "Second memory.")

    result = memory.forget_memories([1, 999, 2])

    assert result == {
        "forgotten": [1, 2],
        "missing": [999],
    }


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
    assert information["categories"] == ["note", "fact"]


def test_capability(database):
    capability = memory.get_capability()

    assert capability["id"] == "memory"
    assert capability["name"] == "Persistent memory"
    assert capability["description"] == "SQLite-backed memory storage"
    assert capability["details"] == {
        "total_memories": 0,
        "categories": [],
    }
