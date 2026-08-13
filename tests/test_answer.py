from alf import answer


def test_prepare_answer_sends_question_and_evidence_to_llm(monkeypatch):
    evidence = [
        {
            "source": "platform",
            "field": "operating_system",
            "value": "Linux",
        }
    ]

    captured = {}

    def fake_ask(answer_request):
        captured["request"] = answer_request
        return "Linux."

    monkeypatch.setattr(
        answer,
        "ask",
        fake_ask,
    )

    result = answer.prepare_answer(
        "What operating system am I running?",
        evidence,
    )

    assert captured["request"] == {
        "question": "What operating system am I running?",
        "evidence": evidence,
    }

    assert result == "Linux."


def test_prepare_answer_sends_empty_evidence_to_llm(monkeypatch):
    captured = {}

    def fake_ask(answer_request):
        captured["request"] = answer_request
        return "I don't know."

    monkeypatch.setattr(
        answer,
        "ask",
        fake_ask,
    )

    result = answer.prepare_answer(
        "What motherboard model does this computer have?",
        [],
    )

    assert captured["request"] == {
        "question": "What motherboard model does this computer have?",
        "evidence": [],
    }

    assert result == "I don't know."
