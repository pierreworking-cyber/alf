from alf import presentation


def test_render_command_structure_error(monkeypatch, capsys):
    monkeypatch.setattr(
        presentation,
        "pause",
        lambda: None,
    )

    presentation.render_command_structure_error("remember")

    output = capsys.readouterr().out

    assert "Improper command structure." in output
    assert "See: alf help remember" in output
    assert "Press Return to continue..." in output


def test_pause_ignores_closed_stdin(monkeypatch):
    def raise_eof():
        raise EOFError

    monkeypatch.setattr("builtins.input", raise_eof)

    presentation.pause()


def test_render_memory_deleted(capsys):
    presentation.render_memory_deleted(12)

    output = capsys.readouterr().out

    assert "Memory 12 deleted." in output


def test_render_memories_deleted(capsys):
    presentation.render_memories_deleted([10, 11, 12])

    output = capsys.readouterr().out

    assert "Memories 10, 11, 12 deleted." in output


def test_render_memory_missing(capsys):
    presentation.render_memory_missing([25, 27])

    output = capsys.readouterr().out

    assert "Memory IDs not found: 25, 27." in output


def test_render_memory_entry_includes_related_memory_ids(capsys):
    presentation.render_memory_entry(
        {
            "id": 58,
            "created": "2026-08-16 03:42:54",
            "category": "note",
            "status": "active",
            "content": "memory links should be displayed against the memory text",
            "related_memory_ids": "46,42",
        }
    )

    output = capsys.readouterr().out

    assert (
        "memory links should be displayed against the memory text (46, 42)"
        in output
    )


def test_render_memory_entry_without_related_memory_ids(capsys):
    presentation.render_memory_entry(
        {
            "id": 58,
            "created": "2026-08-16 03:42:54",
            "category": "note",
            "status": "active",
            "content": "A memory without links.",
            "related_memory_ids": None,
        }
    )

    output = capsys.readouterr().out

    assert "A memory without links." in output
    assert "A memory without links. (" not in output


def test_render_question_includes_source(capsys):
    presentation.render_question(
        "Monkey patching modifies Python code at runtime.",
        "web",
    )

    output = capsys.readouterr().out

    assert "Monkey patching modifies Python code at runtime." in output
    assert "Source: Web" in output


def test_render_question_includes_interpretation_when_different(capsys):
    presentation.render_question(
        "Trailing commas are allowed in Python.",
        "web",
        "Why are trailing commas allowed in Python?",
    )

    output = capsys.readouterr().out

    assert (
        "Question interpreted as: "
        "Why are trailing commas allowed in Python?"
    ) in output
    assert "Trailing commas are allowed in Python." in output


def test_render_question_omits_interpretation_when_unchanged(capsys):
    presentation.render_question(
        "What are microbes?",
        "wikipedia",
        "What are microbes?",
    )

    output = capsys.readouterr().out

    assert "Question interpreted as:" not in output
    assert "What are microbes?" in output


def test_render_question_without_source(capsys):
    presentation.render_question(
        "I couldn't find reliable research.",
    )

    output = capsys.readouterr().out

    assert "I couldn't find reliable research." in output
    assert "Source:" not in output


def test_render_ambiguous_command(capsys):
    presentation.render_ambiguous_command(
        "memor",
        ["memories", "memory"],
    )

    output = capsys.readouterr().out

    assert "Ambiguous command: memor" in output
    assert "Similar options: alf memories, alf memory" in output

def test_render_health_handles_commands_module_failure(capsys):
    report = {
        "checks": [
            {
                "name": "Modules",
                "healthy": True,
                "details": {
                    "failed_modules": [],
                },
            },
            {
                "name": "Commands",
                "healthy": False,
                "details": {
                    "warnings": [
                        {
                            "message": "Commands module could not be loaded",
                        }
                    ],
                },
            },
            {
                "name": "Ollama",
                "healthy": True,
                "details": {},
            },
        ]
    }

    presentation.render_health(report)

    output = capsys.readouterr().out

    assert "Command integrity issues:" in output
    assert "- Commands" in output
    assert "Commands module could not be loaded" in output
