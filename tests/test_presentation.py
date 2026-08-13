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
