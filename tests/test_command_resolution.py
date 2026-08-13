from alf.command_resolution import resolve_category, resolve_command


def test_exact_command_is_resolved():
    assert resolve_command("remember") == "remember"


def test_short_command_prefix_is_resolved():
    assert resolve_command("rem") == "remember"


def test_longer_command_prefix_is_resolved():
    assert resolve_command("reme") == "remember"


def test_memory_category_alias_is_resolved():
    assert resolve_category("notes") == "note"


def test_canonical_memory_category_is_unchanged():
    assert resolve_category("note") == "note"


def test_unknown_command_is_rejected():
    assert resolve_command("make") is None


def test_arbitrary_natural_language_is_not_inferred():
    assert resolve_command("make a memory") is None
