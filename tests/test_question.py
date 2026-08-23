import pytest

from alf import commands, question
from alf.routes import Route


def test_question_command_passes_question_to_question_engine(monkeypatch):
    captured = {}

    result = question.QuestionResult(
        answer="Python's len() function returns the number of items.",
        source="llm",
        research_question="What does Python's len() function return?",
    )

    def fake_answer_question(original_question, verbose=False):
        captured["original_question"] = original_question
        captured["verbose"] = verbose
        return result

    monkeypatch.setattr(
        commands,
        "answer_question",
        fake_answer_question,
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

    assert captured == {
        "original_question": "What does Python's len() function return?",
        "verbose": False,
    }

    assert output == [
        (
            "Python's len() function returns the number of items.",
            "llm",
            "What does Python's len() function return?",
        )
    ]


def test_answer_question_uses_wikipedia_when_research_is_relevant(monkeypatch):
    wikipedia_candidates = [
        {
            "source": "wikipedia",
            "title": "France",
            "page_id": 123,
            "text": "France is a country in Europe.",
        }
    ]

    monkeypatch.setattr(
        question,
        "route",
        lambda question: Route.RESEARCH,
    )

    monkeypatch.setattr(
        question,
        "interpret_question",
        lambda question: question,
    )

    monkeypatch.setattr(
        question,
        "research_wikipedia_candidates",
        lambda question: wikipedia_candidates,
    )

    monkeypatch.setattr(
        question,
        "evaluate_research",
        lambda question, candidates: {
            "relevant": True,
            "candidates": [1],
            "reason": "Relevant.",
        },
    )

    monkeypatch.setattr(
        question,
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
        question,
        "prepare_answer",
        fake_prepare_answer,
    )

    result = question.answer_question(
        "What is the capital of France?"
    )

    assert captured["answer_request"] == {
        "original_question": "What is the capital of France?",
        "research_question": "What is the capital of France?",
        "evidence": [wikipedia_candidates[0]],
        "verbose": False,
    }

    assert result.answer == "Paris."
    assert result.source == "wikipedia"
    assert result.research_question == (
        "What is the capital of France?"
    )


def test_answer_question_uses_web_when_wikipedia_is_not_relevant(monkeypatch):
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
        question,
        "route",
        lambda question: Route.RESEARCH,
    )

    monkeypatch.setattr(
        question,
        "interpret_question",
        lambda question: question,
    )

    monkeypatch.setattr(
        question,
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
        question,
        "evaluate_research",
        fake_evaluate,
    )

    monkeypatch.setattr(
        question,
        "research_web",
        lambda question: web_candidates,
    )

    monkeypatch.setattr(
        question,
        "prepare_answer",
        lambda original_question, research_question, evidence, verbose=False:
        "The film is ...",
    )

    result = question.answer_question(
        "What film is this?"
    )

    assert len(calls) == 2
    assert calls[0] == []
    assert calls[1] == web_candidates

    assert result.answer == "The film is ..."
    assert result.source == "web"
    assert result.research_question == "What film is this?"


def test_answer_question_admits_when_no_research_is_relevant(monkeypatch):
    monkeypatch.setattr(
        question,
        "route",
        lambda question: Route.RESEARCH,
    )

    monkeypatch.setattr(
        question,
        "interpret_question",
        lambda question: question,
    )

    monkeypatch.setattr(
        question,
        "research_wikipedia_candidates",
        lambda question: [],
    )

    monkeypatch.setattr(
        question,
        "research_web",
        lambda question: [],
    )

    monkeypatch.setattr(
        question,
        "evaluate_research",
        lambda question, candidates: {
            "relevant": False,
            "candidates": [],
            "reason": "No reliable evidence.",
        },
    )

    monkeypatch.setattr(
        question,
        "prepare_answer",
        lambda *arguments, **kwargs: pytest.fail(
            "ALF must not answer without evidence"
        ),
    )

    result = question.answer_question(
        "What film is this?"
    )

    assert result.answer == (
        "I couldn't find reliable research that answers your question. "
        "I don't want to guess."
    )
    assert result.source is None
    assert result.research_question == "What film is this?"


def test_answer_question_uses_system_information(monkeypatch):
    system_information = {
        "operating_system": "Linux",
        "hostname": "alf-machine",
        "architecture": "x86_64",
        "python_version": "3.14.6",
    }

    monkeypatch.setattr(
        question,
        "route",
        lambda question: Route.SYSTEM,
    )

    monkeypatch.setattr(
        question,
        "get_system_information",
        lambda: system_information,
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
        return "You are running Linux."

    monkeypatch.setattr(
        question,
        "prepare_answer",
        fake_prepare_answer,
    )

    result = question.answer_question(
        "What operating system am I running?"
    )

    assert captured["answer_request"] == {
        "original_question": "What operating system am I running?",
        "research_question": "What operating system am I running?",
        "evidence": [system_information],
        "verbose": False,
    }

    assert result.answer == "You are running Linux."
    assert result.source == "system"
    assert result.research_question == (
        "What operating system am I running?"
    )


def test_answer_question_uses_memory_when_relevant(monkeypatch):
    memories = [
        {
            "id": 1,
            "category": "decision",
            "status": "active",
            "content": "ALF should use evidence rather than guesses.",
        }
    ]

    monkeypatch.setattr(
        question,
        "route",
        lambda question: Route.MEMORY,
    )

    monkeypatch.setattr(
        question,
        "find_relevant_memories",
        lambda question: memories,
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
        return "We decided to use evidence rather than guesses."

    monkeypatch.setattr(
        question,
        "prepare_answer",
        fake_prepare_answer,
    )

    result = question.answer_question(
        "What did we decide about how ALF should answer questions?"
    )

    assert captured["answer_request"] == {
        "original_question": (
            "What did we decide about how ALF should answer questions?"
        ),
        "research_question": (
            "What did we decide about how ALF should answer questions?"
        ),
        "evidence": memories,
        "verbose": False,
    }

    assert result.answer == (
        "We decided to use evidence rather than guesses."
    )
    assert result.source == "memory"
    assert result.research_question == (
        "What did we decide about how ALF should answer questions?"
    )


def test_answer_question_admits_when_no_memory_matches(monkeypatch):
    monkeypatch.setattr(
        question,
        "route",
        lambda question: Route.MEMORY,
    )

    monkeypatch.setattr(
        question,
        "find_relevant_memories",
        lambda question: [],
    )

    monkeypatch.setattr(
        question,
        "prepare_answer",
        lambda *arguments, **kwargs: pytest.fail(
            "ALF must not answer without memory evidence"
        ),
    )

    result = question.answer_question(
        "What did we decide about something forgotten?"
    )

    assert result.answer == (
        "I couldn't find any relevant memories about that. "
        "I don't want to guess."
    )
    assert result.source is None
    assert result.research_question == (
        "What did we decide about something forgotten?"
    )


def test_answer_question_declines_unsupported_question(monkeypatch):
    monkeypatch.setattr(
        question,
        "route",
        lambda question: Route.DECLINE,
    )

    monkeypatch.setattr(
        question,
        "interpret_question",
        lambda question: pytest.fail(
            "Declined questions must not be interpreted"
        ),
    )

    monkeypatch.setattr(
        question,
        "research_wikipedia_candidates",
        lambda question: pytest.fail(
            "Declined questions must not research Wikipedia"
        ),
    )

    monkeypatch.setattr(
        question,
        "research_web",
        lambda question: pytest.fail(
            "Declined questions must not research the web"
        ),
    )

    monkeypatch.setattr(
        question,
        "prepare_answer",
        lambda *arguments, **kwargs: pytest.fail(
            "Declined questions must not be passed to the LLM"
        ),
    )

    result = question.answer_question(
        "Can you make me a cup of tea?"
    )

    assert result.answer == "I can't help with that."
    assert result.source is None
    assert result.research_question == (
        "Can you make me a cup of tea?"
    )
