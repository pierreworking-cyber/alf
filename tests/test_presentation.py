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


def test_render_memory_forgotten(capsys):
    presentation.render_memory_forgotten(12)

    output = capsys.readouterr().out

    assert "Memory 12 forgotten." in output


def test_render_memories_forgotten(capsys):
    presentation.render_memories_forgotten([10, 11, 12])

    output = capsys.readouterr().out

    assert "Memories 10, 11, 12 forgotten." in output


def test_render_memory_missing(capsys):
    presentation.render_memory_missing([25, 27])

    output = capsys.readouterr().out

    assert "Memory IDs not found: 25, 27." in output


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
