from alf import commands, question
from alf.question_intent import is_action_request


def test_question_command_passes_question_to_question_engine(monkeypatch):
    captured = {}
    output = []

    def fake_answer_question(original_question, verbose=False):
        captured["question"] = original_question
        captured["verbose"] = verbose
        return question.QuestionResult(
            answer="The answer.",
            source="llm",
        )

    monkeypatch.setattr(
        commands,
        "answer_question",
        fake_answer_question,
    )

    monkeypatch.setattr(
        commands,
        "render_question",
        lambda answer, source=None: output.append(
            (answer, source)
        ),
    )

    commands.question_command("What", "is", "Python?")

    assert captured == {
        "question": "What is Python?",
        "verbose": False,
    }
    assert output == [
        ("The answer.", "llm"),
    ]


def test_question_command_passes_verbose_flag(monkeypatch):
    captured = {}

    def fake_answer_question(original_question, verbose=False):
        captured["question"] = original_question
        captured["verbose"] = verbose
        return question.QuestionResult(
            answer="A detailed answer.",
            source="llm",
        )

    monkeypatch.setattr(
        commands,
        "answer_question",
        fake_answer_question,
    )

    monkeypatch.setattr(
        commands,
        "render_question",
        lambda answer, source=None: None,
    )

    commands.question_command(
        "Explain",
        "Python",
        "--verbose",
    )

    assert captured == {
        "question": "Explain Python",
        "verbose": True,
    }


def test_answer_question_sends_question_to_answer_layer(monkeypatch):
    captured = {}

    def fake_prepare_answer(original_question, verbose=False):
        captured["question"] = original_question
        captured["verbose"] = verbose
        return "The answer."

    monkeypatch.setattr(
        question,
        "prepare_answer",
        fake_prepare_answer,
    )

    result = question.answer_question("What is Python?")

    assert result.answer == "The answer."
    assert result.source == "llm"
    assert captured == {
        "question": "What is Python?",
        "verbose": False,
    }


def test_answer_question_passes_verbose_flag(monkeypatch):
    captured = {}

    def fake_prepare_answer(original_question, verbose=False):
        captured["question"] = original_question
        captured["verbose"] = verbose
        return "A detailed answer."

    monkeypatch.setattr(
        question,
        "prepare_answer",
        fake_prepare_answer,
    )

    result = question.answer_question(
        "Explain Python",
        verbose=True,
    )

    assert result.answer == "A detailed answer."
    assert result.source == "llm"
    assert captured == {
        "question": "Explain Python",
        "verbose": True,
    }


def test_answer_question_reports_progress(monkeypatch):
    progress_messages = []

    monkeypatch.setattr(
        question,
        "prepare_answer",
        lambda original_question, verbose=False: "The answer.",
    )

    result = question.answer_question(
        "What is Python?",
        progress=progress_messages.append,
    )

    assert result.answer == "The answer."
    assert result.source == "llm"
    assert progress_messages == ["Asking language model…"]



def test_action_request_is_detected():
    assert is_action_request("Make me a cup of tea")
    assert is_action_request("Delete /tmp/")
    assert is_action_request("restart the computer")


def test_explanatory_request_is_not_an_action():
    assert not is_action_request("How do I delete /tmp?")
    assert not is_action_request("What does rm -rf do?")
    assert not is_action_request("How can I restart the computer?")


def test_normal_question_is_not_an_action():
    assert not is_action_request("What's the capital of France?")
    assert not is_action_request("Who wrote The Moon's a Balloon?")

def test_answer_question_passes_research_evidence_to_answer_layer(
    monkeypatch,
):
    captured = {}

    monkeypatch.setattr(
        question,
        "needs_research",
        lambda original_question: True,
    )

    monkeypatch.setattr(
        question,
        "research",
        lambda original_question, timings=None: [
            {
                "title": "Source A",
                "url": "https://example.com/a",
                "domain": "example.com",
                "text": "Evidence supporting claim A.",
                "score": 10.0,
            },
        ],
    )

    monkeypatch.setattr(
        question,
        "evaluate_evidence",
        lambda original_question, candidates: {
            "answer": "Claim A is the best-supported answer.",
            "confidence": "high",
            "supporting_candidates": [1],
            "rejected_candidates": [],
            "reason": "Source A directly supports claim A.",
        },
    )

    monkeypatch.setattr(
        question,
        "select_evidence",
        lambda candidates, evaluation: candidates,
    )

    def fake_prepare_answer(
        original_question,
        evidence=None,
        verbose=False,
        **kwargs,
    ):
        captured["question"] = original_question
        captured["evidence"] = evidence
        captured["verbose"] = verbose
        return "The researched answer."

    monkeypatch.setattr(
        question,
        "prepare_answer",
        fake_prepare_answer,
    )

    result = question.answer_question(
        "Why did this happen?",
    )

    assert result.answer == "The researched answer."
    assert result.source == "research"
    assert captured["question"] == "Why did this happen?"
    assert captured["evidence"] == [
        {
            "title": "Source A",
            "url": "https://example.com/a",
            "domain": "example.com",
            "text": "Evidence supporting claim A.",
            "score": 10.0,
        },
    ]
    assert captured["verbose"] is False


def test_answer_question_passes_research_judgement_to_answer_layer(
    monkeypatch,
):
    captured = {}

    monkeypatch.setattr(
        question,
        "needs_research",
        lambda original_question: True,
    )

    monkeypatch.setattr(
        question,
        "research",
        lambda original_question, timings=None: [
            {
                "title": "Source A",
                "url": "https://example.com/a",
                "domain": "example.com",
                "text": "Evidence supporting claim A.",
                "score": 10.0,
            },
        ],
    )

    evaluation = {
        "answer": "Claim A is the best-supported answer.",
        "confidence": "high",
        "supporting_candidates": [1],
        "rejected_candidates": [],
        "reason": "Source A directly supports claim A.",
    }

    monkeypatch.setattr(
        question,
        "evaluate_evidence",
        lambda original_question, candidates: evaluation,
    )

    monkeypatch.setattr(
        question,
        "select_evidence",
        lambda candidates, evaluation: candidates,
    )

    def fake_prepare_answer(
        original_question,
        evidence=None,
        verbose=False,
        **kwargs,
    ):
        captured["question"] = original_question
        captured["evidence"] = evidence
        captured["kwargs"] = kwargs
        return "The researched answer."

    monkeypatch.setattr(
        question,
        "prepare_answer",
        fake_prepare_answer,
    )

    result = question.answer_question(
        "Why did this happen?",
    )

    assert result.answer == "The researched answer."
    assert result.source == "research"
    assert captured["kwargs"]["research_judgement"] == (
        "Claim A is the best-supported answer."
    )

