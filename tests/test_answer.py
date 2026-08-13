from alf.answer import prepare_answer


def test_prepare_answer_combines_question_and_evidence():
    evidence = [
        {
            "source": "platform",
            "field": "operating_system",
            "value": "Linux",
        }
    ]

    result = prepare_answer(
        "What operating system am I running?",
        evidence,
    )

    assert result == {
        "question": "What operating system am I running?",
        "evidence": evidence,
    }


def test_prepare_answer_accepts_no_evidence():
    result = prepare_answer(
        "What motherboard model does this computer have?",
        [],
    )

    assert result == {
        "question": "What motherboard model does this computer have?",
        "evidence": [],
    }
