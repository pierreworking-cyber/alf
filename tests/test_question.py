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
