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
        "What operating system am I running?",
        evidence,
    )

    assert captured["request"] == {
        "question": "What operating system am I running?",
        "research_question": "What operating system am I running?",
        "evidence": evidence,
        "verbose": False,
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
        "What motherboard model does this computer have?",
        [],
    )

    assert captured["request"] == {
        "question": "What motherboard model does this computer have?",
        "research_question": "What motherboard model does this computer have?",
        "evidence": [],
        "verbose": False,
    }

    assert result == "I don't know."


def test_prepare_answer_sends_verbose_to_llm(monkeypatch):
    captured = {}

    def fake_ask(answer_request):
        captured["request"] = answer_request
        return "A detailed answer."

    monkeypatch.setattr(
        answer,
        "ask",
        fake_ask,
    )

    result = answer.prepare_answer(
        "What are microbes?",
        "What are microbes?",
        [{"source": "wikipedia", "text": "Microbes are microscopic organisms."}],
        verbose=True,
    )

    assert captured["request"] == {
        "question": "What are microbes?",
        "research_question": "What are microbes?",
        "evidence": [
            {
                "source": "wikipedia",
                "text": "Microbes are microscopic organisms.",
            }
        ],
        "verbose": True,
    }

    assert result == "A detailed answer."
