import pytest

from alf import answer, commands


def test_question_command_uses_wikipedia_when_research_is_relevant(monkeypatch):
    wikipedia_candidates = [
        {
            "source": "wikipedia",
            "title": "France",
            "page_id": 123,
            "text": "France is a country in Europe.",
        }
    ]

    monkeypatch.setattr(
        commands,
        "research_wikipedia_candidates",
        lambda question: wikipedia_candidates,
    )

    monkeypatch.setattr(
        commands,
        "evaluate_research",
        lambda question, candidates: {
            "relevant": True,
            "candidates": [1],
            "reason": "Relevant.",
        },
    )

    monkeypatch.setattr(
        commands,
        "research_web",
        lambda question: pytest.fail(
            "Web search should not be used"
        ),
    )

    captured = {}

    def fake_ask(answer_request):
        captured["answer_request"] = answer_request
        return "Paris."

    monkeypatch.setattr(
        answer,
        "ask",
        fake_ask,
    )

    output = []

    monkeypatch.setattr(
        commands,
        "render_question",
        lambda answer, source: output.append((answer, source)),
    )

    commands.question_command(
        "What",
        "is",
        "the",
        "capital",
        "of",
        "France?",
    )

    assert captured["answer_request"] == {
        "question": "What is the capital of France?",
        "evidence": [wikipedia_candidates[0]],
    }
    assert output == [("Paris.", "wikipedia")]


def test_question_command_uses_web_when_wikipedia_is_not_relevant(monkeypatch):
    web_candidates = [
        {
            "source": "web",
            "title": "Film information",
            "url": "https://example.com/film",
            "text": "Children encounter a homeless man.",
        }
    ]

    calls = []

    monkeypatch.setattr(
        commands,
        "research_wikipedia_candidates",
        lambda question: [],
    )

    def fake_evaluate(question, candidates):
        calls.append(candidates)

        if candidates == []:
            return {
                "relevant": False,
                "candidates": [],
                "reason": "No relevant Wikipedia evidence.",
            }

        return {
            "relevant": True,
            "candidates": [1],
            "reason": "Relevant web evidence.",
        }

    monkeypatch.setattr(
        commands,
        "evaluate_research",
        fake_evaluate,
    )

    monkeypatch.setattr(
        commands,
        "research_web",
        lambda question: web_candidates,
    )

    monkeypatch.setattr(
        answer,
        "ask",
        lambda answer_request: "The film is ...",
    )

    output = []

    monkeypatch.setattr(
        commands,
        "render_question",
        lambda answer, source: output.append((answer, source)),
    )

    commands.question_command("What", "film", "is", "this?")

    assert len(calls) == 2
    assert calls[0] == []
    assert calls[1] == web_candidates
    assert output == [("The film is ...", "web")]


def test_question_command_admits_when_no_research_is_relevant(monkeypatch):
    monkeypatch.setattr(
        commands,
        "research_wikipedia_candidates",
        lambda question: [],
    )

    monkeypatch.setattr(
        commands,
        "research_web",
        lambda question: [],
    )

    monkeypatch.setattr(
        commands,
        "evaluate_research",
        lambda question, candidates: {
            "relevant": False,
            "candidates": [],
            "reason": "No reliable evidence.",
        },
    )

    monkeypatch.setattr(
        answer,
        "ask",
        lambda answer_request: pytest.fail(
            "ALF must not answer without evidence"
        ),
    )

    output = []

    monkeypatch.setattr(
        commands,
        "render_question",
        lambda answer, source=None: output.append(
            (answer, source)
        ),
    )

    commands.question_command("What", "film", "is", "this?")

    assert output == [
        (
            "I couldn't find reliable research that answers your question. "
            "I don't want to guess.",
            None,
        )
    ]

def test_interpret_memory_selection_accepts_single_id():
    assert commands.interpret_memory_selection("26") == [26]


def test_interpret_memory_selection_expands_range():
    assert commands.interpret_memory_selection("23-26") == [
        23,
        24,
        25,
        26,
    ]


def test_interpret_memory_selection_accepts_reversed_range():
    assert commands.interpret_memory_selection("26-23") == [
        23,
        24,
        25,
        26,
    ]


def test_interpret_memory_selection_accepts_multiple_ranges_and_ids():
    assert commands.interpret_memory_selection("10-12,15,20-21") == [
        10,
        11,
        12,
        15,
        20,
        21,
    ]


def test_interpret_memory_selection_removes_duplicates():
    assert commands.interpret_memory_selection("10-12,11,12-13") == [
        10,
        11,
        12,
        13,
    ]


def test_interpret_memory_selection_rejects_invalid_selection():
    assert commands.interpret_memory_selection("10--12") is None
    assert commands.interpret_memory_selection("10-banana") is None
    assert commands.interpret_memory_selection("0") is None
    assert commands.interpret_memory_selection("10,") is None


def test_interpret_memory_selection_rejects_negative_id():
    assert commands.interpret_memory_selection("-12") is None


def test_forget_command_forgets_single_memory(monkeypatch):
    captured = {}

    monkeypatch.setattr(
        commands,
        "forget_memories",
        lambda memory_ids: {
            "forgotten": memory_ids,
            "missing": [],
        },
    )

    monkeypatch.setattr(
        commands,
        "render_memory_forgotten",
        lambda memory_id: captured.setdefault(
            "forgotten",
            memory_id,
        ),
    )

    commands.forget_command("26")

    assert captured == {
        "forgotten": 26,
    }


def test_forget_command_forgets_memory_range(monkeypatch):
    captured = {}

    def fake_forget_memories(memory_ids):
        captured["memory_ids"] = memory_ids
        return {
            "forgotten": memory_ids,
            "missing": [],
        }

    monkeypatch.setattr(
        commands,
        "forget_memories",
        fake_forget_memories,
    )

    monkeypatch.setattr(
        commands,
        "render_memories_forgotten",
        lambda memory_ids: captured.setdefault(
            "forgotten",
            memory_ids,
        ),
    )

    commands.forget_command("23-26")

    assert captured["memory_ids"] == [23, 24, 25, 26]
    assert captured["forgotten"] == [23, 24, 25, 26]


def test_forget_command_reports_missing_memories(monkeypatch):
    output = []

    monkeypatch.setattr(
        commands,
        "forget_memories",
        lambda memory_ids: {
            "forgotten": [23, 24],
            "missing": [25],
        },
    )

    monkeypatch.setattr(
        commands,
        "render_memories_forgotten",
        lambda memory_ids: output.append(
            ("forgotten", memory_ids)
        ),
    )

    monkeypatch.setattr(
        commands,
        "render_memory_missing",
        lambda memory_ids: output.append(
            ("missing", memory_ids)
        ),
    )

    commands.forget_command("23-25")

    assert output == [
        ("forgotten", [23, 24]),
        ("missing", [25]),
    ]


def test_forget_command_rejects_invalid_selection(monkeypatch):
    output = []

    monkeypatch.setattr(
        commands,
        "render_command_structure_error",
        lambda command: output.append(command),
    )

    commands.forget_command("-12")

    assert output == ["forget"]
