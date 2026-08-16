import pytest

from alf import answer, commands
from alf.routes import Route


def test_question_command_uses_llm_when_route_is_llm(monkeypatch):
    captured = {}

    monkeypatch.setattr(
        commands,
        "route",
        lambda question: Route.LLM,
    )

    def fake_prepare_answer(
        original_question,
        research_question,
        evidence,
        verbose=False,
    ):
        captured["answer_request"] = {
            "original_question": original_question,
            "research_question": research_question,
            "evidence": evidence,
            "verbose": verbose,
        }
        return "Python's len() function returns the number of items."

    monkeypatch.setattr(
        commands,
        "prepare_answer",
        fake_prepare_answer,
    )

    monkeypatch.setattr(
        commands,
        "research_wikipedia_candidates",
        lambda question: pytest.fail(
            "Wikipedia research should not be used"
        ),
    )

    monkeypatch.setattr(
        commands,
        "research_web",
        lambda question: pytest.fail(
            "Web research should not be used"
        ),
    )

    output = []

    monkeypatch.setattr(
        commands,
        "render_question",
        lambda answer, source, research_question: output.append(
            (answer, source, research_question)
        ),
    )

    commands.question_command(
        "What",
        "does",
        "Python's",
        "len()",
        "function",
        "return?",
    )

    assert captured["answer_request"] == {
        "original_question": "What does Python's len() function return?",
        "research_question": "What does Python's len() function return?",
        "evidence": [],
        "verbose": False,
    }

    assert output == [
        (
            "Python's len() function returns the number of items.",
            "llm",
            "What does Python's len() function return?",
        )
    ]


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
        "route",
        lambda question: Route.RESEARCH,
    )

    monkeypatch.setattr(
        commands,
        "interpret_question",
        lambda question: question,
    )

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

    def fake_prepare_answer(
        original_question,
        research_question,
        evidence,
        verbose=False,
    ):
        captured["answer_request"] = {
            "original_question": original_question,
            "research_question": research_question,
            "evidence": evidence,
            "verbose": verbose,
        }
        return "Paris."

    monkeypatch.setattr(
        commands,
        "prepare_answer",
        fake_prepare_answer,
    )

    output = []

    monkeypatch.setattr(
        commands,
        "render_question",
        lambda answer, source, research_question: output.append(
            (answer, source, research_question)
        ),
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
        "original_question": "What is the capital of France?",
        "research_question": "What is the capital of France?",
        "evidence": [wikipedia_candidates[0]],
        "verbose": False,
    }
    assert output == [
        (
            "Paris.",
            "wikipedia",
            "What is the capital of France?",
        )
    ]


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
        "route",
        lambda question: Route.RESEARCH,
    )
    monkeypatch.setattr(
        commands,
        "interpret_question",
        lambda question: question,
    )

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

    def fake_prepare_answer(
        original_question,
        research_question,
        evidence,
        verbose=False,
    ):
        return "The film is ..."

    monkeypatch.setattr(
        commands,
        "prepare_answer",
        fake_prepare_answer,
    )

    output = []

    monkeypatch.setattr(
        commands,
        "render_question",
        lambda answer, source, research_question: output.append(
            (answer, source, research_question)
        ),
    )

    commands.question_command("What", "film", "is", "this?")

    assert len(calls) == 2
    assert calls[0] == []
    assert calls[1] == web_candidates
    assert output == [
        (
            "The film is ...",
            "web",
            "What film is this?",
        )
    ]


def test_question_command_admits_when_no_research_is_relevant(monkeypatch):
    monkeypatch.setattr(
        commands,
        "route",
        lambda question: Route.RESEARCH,
    )

    monkeypatch.setattr(
        commands,
        "interpret_question",
        lambda question: question,
    )

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


def test_question_command_accepts_verbose_option(monkeypatch):
    captured = {}

    monkeypatch.setattr(
        commands,
        "research_wikipedia_candidates",
        lambda question: [
            {
                "source": "wikipedia",
                "title": "Microbe",
                "text": "Microbes are microscopic organisms.",
            }
        ],
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

    def fake_prepare_answer(
        original_question,
        research_question,
        evidence,
        verbose=False,
    ):
        captured["verbose"] = verbose
        return "A detailed answer."

    monkeypatch.setattr(
        commands,
        "prepare_answer",
        fake_prepare_answer,
    )

    monkeypatch.setattr(
        commands,
        "render_question",
        lambda answer, source, research_question=None: None,
    )

    commands.question_command(
        "-v",
        "What",
        "are",
        "microbes?",
    )

    assert captured["verbose"] is True


def test_question_command_accepts_long_verbose_option(monkeypatch):
    captured = {}

    monkeypatch.setattr(
        commands,
        "research_wikipedia_candidates",
        lambda question: [
            {
                "source": "wikipedia",
                "title": "Microbe",
                "text": "Microbes are microscopic organisms.",
            }
        ],
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

    def fake_prepare_answer(
        original_question,
        research_question,
        evidence,
        verbose=False,
    ):
        captured["verbose"] = verbose
        return "A detailed answer."

    monkeypatch.setattr(
        commands,
        "prepare_answer",
        fake_prepare_answer,
    )

    monkeypatch.setattr(
        commands,
        "render_question",
        lambda answer, source, research_question=None: None,
    )

    commands.question_command(
        "What",
        "are",
        "microbes?",
        "--verbose",
    )

    assert captured["verbose"] is True


def test_question_command_keeps_verbose_text_inside_question(monkeypatch):
    captured = {}

    monkeypatch.setattr(
        commands,
        "interpret_question",
        lambda question: question,
    )

    monkeypatch.setattr(
        commands,
        "research_wikipedia_candidates",
        lambda question: [
            {
                "source": "wikipedia",
                "title": "Linux commands",
                "text": "Many Linux commands provide a -v option.",
            }
        ],
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

    def fake_prepare_answer(
        original_question,
        research_question,
        evidence,
        verbose=False,
    ):
        captured["question"] = original_question
        captured["verbose"] = verbose
        return "An answer."

    monkeypatch.setattr(
        commands,
        "prepare_answer",
        fake_prepare_answer,
    )

    monkeypatch.setattr(
        commands,
        "render_question",
        lambda answer, source, research_question=None: None,
    )

    commands.question_command(
        "What Linux commands have the switch -v",
    )

    assert captured["question"] == (
        "What Linux commands have the switch -v"
    )
    assert captured["verbose"] is False


def test_question_command_rejects_unknown_option(monkeypatch):
    output = []

    monkeypatch.setattr(
        commands,
        "render_command_structure_error",
        lambda command: output.append(command),
    )

    monkeypatch.setattr(
        commands,
        "research_wikipedia_candidates",
        lambda question: pytest.fail(
            "Research should not be performed"
        ),
    )

    commands.question_command(
        "--banana",
        "What",
        "are",
        "microbes?",
    )

    assert output == ["question"]


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


def test_relate_command_accepts_multiple_memory_ids(monkeypatch):
    captured = []

    monkeypatch.setattr(
        commands,
        "relate_memory",
        lambda memory_id, related_memory_ids: (
            captured.append(
                {
                    "memory_id": memory_id,
                    "related_memory_ids": related_memory_ids,
                }
            )
            or related_memory_ids
        ),
    )

    monkeypatch.setattr(
        commands,
        "render_memory_related",
        lambda memory_id, related_memory_ids: None,
    )

    commands.relate_command(
        "47",
        "46,43",
    )

    commands.relate_command(
        "47",
        "46-43,52",
    )

    assert captured == [
        {
            "memory_id": 47,
            "related_memory_ids": "46,43",
        },
        {
            "memory_id": 47,
            "related_memory_ids": "43,44,45,46,52",
        },
    ]


def test_relate_command_rejects_invalid_memory_selection(monkeypatch):
    output = []

    monkeypatch.setattr(
        commands,
        "render_invalid_related_memory",
        lambda related_memory_ids, usage: output.append(
            (related_memory_ids, usage)
        ),
    )

    monkeypatch.setattr(
        commands,
        "relate_memory",
        lambda *arguments: pytest.fail(
            "relate_memory should not be called"
        ),
    )

    commands.relate_command(
        "47",
        "46--43",
    )

    assert output == [
        (
            "46--43",
            "alf relate <id> <ids>",
        )
    ]


def test_archive_command_archives_single_memory(monkeypatch):
    captured = []

    monkeypatch.setattr(
        commands,
        "archive_memories",
        lambda memory_ids: (
            captured.append(memory_ids)
            or {
                "archived": memory_ids,
                "missing": [],
            }
        ),
    )

    monkeypatch.setattr(
        commands,
        "render_memory_archived",
        lambda memory_id: None,
    )

    commands.archive_command("47")

    assert captured == [[47]]


def test_archive_command_archives_memory_selection(monkeypatch):
    captured = []

    monkeypatch.setattr(
        commands,
        "archive_memories",
        lambda memory_ids: (
            captured.append(memory_ids)
            or {
                "archived": memory_ids,
                "missing": [],
            }
        ),
    )

    monkeypatch.setattr(
        commands,
        "render_memories_archived",
        lambda memory_ids: None,
    )

    commands.archive_command("46-43,52")

    assert captured == [[43, 44, 45, 46, 52]]


def test_archive_command_rejects_invalid_memory_selection(monkeypatch):
    output = []

    monkeypatch.setattr(
        commands,
        "render_command_structure_error",
        lambda command: output.append(command),
    )

    monkeypatch.setattr(
        commands,
        "archive_memories",
        lambda *arguments: pytest.fail(
            "archive_memories should not be called"
        ),
    )

    commands.archive_command("46--43")

    assert output == ["archive"]
