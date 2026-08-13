from alf import commands


def test_run_resolves_short_command_prefix(monkeypatch):
    captured = {}

    def fake_remember_command(*arguments):
        captured["arguments"] = arguments

    monkeypatch.setitem(
        commands.command_handlers,
        "remember",
        fake_remember_command,
    )

    assert commands.run("rem", ["note", "Dave is fictional"]) is True

    assert captured["arguments"] == (
        "note",
        "Dave is fictional",
    )


def test_run_resolves_longer_command_prefix(monkeypatch):
    captured = {}

    def fake_remember_command(*arguments):
        captured["arguments"] = arguments

    monkeypatch.setitem(
        commands.command_handlers,
        "remember",
        fake_remember_command,
    )

    assert commands.run("reme", ["note", "Dave is fictional"]) is True

    assert captured["arguments"] == (
        "note",
        "Dave is fictional",
    )


def test_run_rejects_unknown_natural_language_command():
    assert commands.run("make", ["a", "memory", "Dave is fictional"]) is False


def test_run_resolves_category_alias(monkeypatch):
    captured = {}

    def fake_remember_command(*arguments):
        captured["arguments"] = arguments

    monkeypatch.setitem(
        commands.command_handlers,
        "remember",
        fake_remember_command,
    )

    assert commands.run(
        "rem",
        ["notes", "Dave is fictional"],
    ) is True

    assert captured["arguments"] == (
        "notes",
        "Dave is fictional",
    )


def test_run_rejects_unknown_command():
    assert commands.run(
        "make",
        ["a", "memory"],
    ) is False


def test_remember_command_resolves_category_prefix(monkeypatch):
    captured = {}

    monkeypatch.setattr(
        commands,
        "get_memory_categories",
        lambda: ["note", "fact", "decision", "preference"],
    )

    def fake_remember(category, content, related_memory_ids=None):
        captured["category"] = category
        captured["content"] = content
        captured["related_memory_ids"] = related_memory_ids
        return True

    monkeypatch.setattr(
        commands,
        "remember",
        fake_remember,
    )

    monkeypatch.setattr(
        commands,
        "render_memory_saved",
        lambda category: captured.setdefault("saved", category),
    )

    commands.remember_command(
        "notes",
        "Dave is fictional",
    )

    assert captured["category"] == "note"
    assert captured["content"] == "Dave is fictional"
    assert captured["related_memory_ids"] is None
    assert captured["saved"] == "note"


def test_remember_command_rejects_unknown_category(monkeypatch):
    output = []

    monkeypatch.setattr(
        commands,
        "get_memory_categories",
        lambda: ["note", "fact", "decision", "preference"],
    )

    monkeypatch.setattr(
        commands,
        "render_invalid_memory_category",
        lambda category, categories: output.append(
            (category, categories)
        ),
    )

    commands.remember_command(
        "banana",
        "Dave is fictional",
    )

    assert output == [
        (
            "banana",
            ["note", "fact", "decision", "preference"],
        )
    ]


def test_run_resolves_command_and_category_together(monkeypatch):
    captured = {}

    def fake_remember(category, content, related_memory_ids=None):
        captured["category"] = category
        captured["content"] = content
        captured["related_memory_ids"] = related_memory_ids
        return True

    monkeypatch.setattr(
        commands,
        "remember",
        fake_remember,
    )

    monkeypatch.setattr(
        commands,
        "render_memory_saved",
        lambda category: captured.setdefault("saved", category),
    )

    assert commands.run(
        "reme",
        ["notes", "Dave is fictional"],
    ) is True

    assert captured["category"] == "note"
    assert captured["content"] == "Dave is fictional"
    assert captured["related_memory_ids"] is None
    assert captured["saved"] == "note"


def test_remember_accepts_positional_category_and_long_related_option(monkeypatch):
    captured = {}

    def fake_remember(category, content, related_memory_ids=None):
        captured["category"] = category
        captured["content"] = content
        captured["related_memory_ids"] = related_memory_ids
        return True

    monkeypatch.setattr(commands, "remember", fake_remember)
    monkeypatch.setattr(
        commands,
        "render_memory_saved",
        lambda category: captured.setdefault("saved", category),
    )

    assert commands.run(
        "rem",
        ["notes", "Dave is fictional", "--relate", "41"],
    ) is True

    assert captured["category"] == "note"
    assert captured["content"] == "Dave is fictional"
    assert captured["related_memory_ids"] == "41"


def test_remember_accepts_option_category_and_short_related_option(monkeypatch):
    captured = {}

    def fake_remember(category, content, related_memory_ids=None):
        captured["category"] = category
        captured["content"] = content
        captured["related_memory_ids"] = related_memory_ids
        return True

    monkeypatch.setattr(commands, "remember", fake_remember)
    monkeypatch.setattr(
        commands,
        "render_memory_saved",
        lambda category: captured.setdefault("saved", category),
    )

    assert commands.run(
        "rem",
        ["-c", "note", "Dave is fictional", "-r", "41"],
    ) is True

    assert captured["category"] == "note"
    assert captured["content"] == "Dave is fictional"
    assert captured["related_memory_ids"] == "41"


def test_remember_accepts_long_category_option(monkeypatch):
    captured = {}

    def fake_remember(category, content, related_memory_ids=None):
        captured["category"] = category
        captured["content"] = content
        captured["related_memory_ids"] = related_memory_ids
        return True

    monkeypatch.setattr(commands, "remember", fake_remember)
    monkeypatch.setattr(
        commands,
        "render_memory_saved",
        lambda category: captured.setdefault("saved", category),
    )

    assert commands.run(
        "rem",
        ["--category", "note", "Dave is fictional"],
    ) is True

    assert captured["category"] == "note"
    assert captured["content"] == "Dave is fictional"
    assert captured["related_memory_ids"] is None


def test_remember_rejects_category_option_without_value(monkeypatch):
    output = []

    monkeypatch.setattr(
        commands,
        "render_command_structure_error",
        lambda command: output.append(command),
    )

    assert commands.run(
        "rem",
        ["--category"],
    ) is True

    assert output == ["remember"]


def test_remember_rejects_related_option_without_value(monkeypatch):
    output = []

    monkeypatch.setattr(
        commands,
        "render_command_structure_error",
        lambda command: output.append(command),
    )

    assert commands.run(
        "rem",
        ["note", "Dave is fictional", "--relate"],
    ) is True

    assert output == ["remember"]


def test_remember_rejects_unknown_option(monkeypatch):
    output = []

    monkeypatch.setattr(
        commands,
        "render_command_structure_error",
        lambda command: output.append(command),
    )

    assert commands.run(
        "rem",
        ["note", "Dave is fictional", "--banana"],
    ) is True

    assert output == ["remember"]


def test_remember_rejects_duplicate_category_specification(monkeypatch):
    output = []

    monkeypatch.setattr(
        commands,
        "render_command_structure_error",
        lambda command: output.append(command),
    )

    assert commands.run(
        "rem",
        ["note", "Dave is fictional", "--category", "fact"],
    ) is True

    assert output == ["remember"]


def test_remember_rejects_category_option_without_content(monkeypatch):
    output = []

    monkeypatch.setattr(
        commands,
        "render_command_structure_error",
        lambda command: output.append(command),
    )

    assert commands.run(
        "rem",
        ["--category", "note"],
    ) is True

    assert output == ["remember"]


def test_memories_accepts_short_category_option(monkeypatch):
    captured = {}

    monkeypatch.setattr(
        commands,
        "get_memories",
        lambda options: captured.setdefault("options", options) or [],
    )
    monkeypatch.setattr(
        commands,
        "render_memories",
        lambda memories, options: None,
    )

    commands.memories_command(
        "-c",
        "pref",
    )

    assert captured["options"]["category"] == "preference"


def test_search_accepts_short_category_option(monkeypatch):
    captured = {}

    monkeypatch.setattr(
        commands,
        "search_memories",
        lambda term, options: captured.setdefault("options", options) or [],
    )
    monkeypatch.setattr(
        commands,
        "render_memories",
        lambda memories, options: None,
    )

    commands.search_command(
        "Peter",
        "-c",
        "pref",
    )

    assert captured["options"]["category"] == "preference"


def test_memories_accepts_short_all_option(monkeypatch):
    captured = {}

    monkeypatch.setattr(
        commands,
        "get_memories",
        lambda options: captured.setdefault("options", options) or [],
    )
    monkeypatch.setattr(
        commands,
        "render_memories",
        lambda memories, options: None,
    )

    commands.memories_command("-a")

    assert captured["options"]["include_archived"] is True


def test_memories_accepts_short_group_option(monkeypatch):
    captured = {}

    monkeypatch.setattr(
        commands,
        "get_memories",
        lambda options: captured.setdefault("options", options) or [],
    )
    monkeypatch.setattr(
        commands,
        "render_memories",
        lambda memories, options: None,
    )

    commands.memories_command(
        "-g",
        "category",
    )

    assert captured["options"]["group"] == "category"


def test_memories_rejects_unknown_short_category_option(monkeypatch):
    output = []

    monkeypatch.setattr(
        commands,
        "render_invalid_memory_category",
        lambda category, categories: output.append(
            (category, categories)
        ),
    )

    commands.memories_command(
        "-c",
        "banana",
    )

    assert output == [
        (
            "banana",
            ["note", "fact", "decision", "preference"],
        )
    ]


def test_search_rejects_unknown_short_category_option(monkeypatch):
    output = []

    monkeypatch.setattr(
        commands,
        "render_invalid_memory_category",
        lambda category, categories: output.append(
            (category, categories)
        ),
    )

    commands.search_command(
        "Peter",
        "-c",
        "banana",
    )

    assert output == [
        (
            "banana",
            ["note", "fact", "decision", "preference"],
        )
    ]
