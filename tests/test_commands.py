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
        lambda answer: output.append(answer),
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

    assert output == ["Paris."]


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
        lambda answer: output.append(answer),
    )

    commands.question_command("What", "film", "is", "this?")

    assert len(calls) == 2
    assert calls[0] == []
    assert calls[1] == web_candidates
    assert output == ["The film is ..."]


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
        lambda answer: output.append(answer),
    )

    commands.question_command("What", "film", "is", "this?")

    assert output == [
        "I couldn't find reliable research that answers your question. "
        "I don't want to guess."
    ]
