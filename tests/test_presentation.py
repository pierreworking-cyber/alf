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
