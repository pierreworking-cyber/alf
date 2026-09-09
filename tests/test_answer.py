from alf import answer


def test_prepare_answer_preserves_user_question(monkeypatch):
    captured = {}

    def fake_ask(answer_request):
        captured["request"] = answer_request
        return "answer"

    monkeypatch.setattr(answer, "ask", fake_ask)

    result = answer.prepare_answer("What is Python?")

    assert result == "answer"
    assert captured["request"]["question"] == "What is Python?"


def test_prepare_answer_defaults_to_non_verbose(monkeypatch):
    captured = {}

    def fake_ask(answer_request):
        captured["request"] = answer_request
        return "answer"

    monkeypatch.setattr(answer, "ask", fake_ask)

    answer.prepare_answer("What is Python?")

    assert captured["request"]["verbose"] is False


def test_prepare_answer_passes_verbose_true(monkeypatch):
    captured = {}

    def fake_ask(answer_request):
        captured["request"] = answer_request
        return "answer"

    monkeypatch.setattr(answer, "ask", fake_ask)

    answer.prepare_answer("Explain Python", verbose=True)

    assert captured["request"]["verbose"] is True


def test_prepare_answer_returns_llm_answer_unchanged(monkeypatch):
    expected = (
        "Python is a programming language. "
        "It is commonly used for automation and data analysis."
    )

    def fake_ask(answer_request):
        return expected

    monkeypatch.setattr(answer, "ask", fake_ask)

    result = answer.prepare_answer("What is Python?")

    assert result == expected
