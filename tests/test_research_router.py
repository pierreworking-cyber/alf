from alf.research_router import needs_research


def test_stable_knowledge_does_not_need_research(monkeypatch):
    def fake_generate_json(prompt):
        return {
            "route": "LLM",
            "reason": "Stable general knowledge.",
        }

    monkeypatch.setattr(
        "alf.research_router.generate_json",
        fake_generate_json,
    )

    assert not needs_research("What is RAM?")


def test_current_information_needs_research(monkeypatch):
    def fake_generate_json(prompt):
        return {
            "route": "RESEARCH",
            "reason": "The answer can change over time.",
        }

    monkeypatch.setattr(
        "alf.research_router.generate_json",
        fake_generate_json,
    )

    assert needs_research(
        "Who is the current Prime Minister of the UK?"
    )


def test_router_passes_question_to_model(monkeypatch):
    captured = {}

    def fake_generate_json(prompt):
        captured["prompt"] = prompt
        return {
            "route": "LLM",
            "reason": "Stable knowledge.",
        }

    monkeypatch.setattr(
        "alf.research_router.generate_json",
        fake_generate_json,
    )

    needs_research("What is Python?")

    assert "What is Python?" in captured["prompt"]


def test_router_returns_false_for_llm_route(monkeypatch):
    monkeypatch.setattr(
        "alf.research_router.generate_json",
        lambda prompt: {
            "route": "LLM",
            "reason": "Stable knowledge.",
        },
    )

    assert needs_research("Explain how RAM works.") is False


def test_router_returns_true_for_research_route(monkeypatch):
    monkeypatch.setattr(
        "alf.research_router.generate_json",
        lambda prompt: {
            "route": "RESEARCH",
            "reason": "Current information.",
        },
    )

    assert needs_research("What is the current UK inflation rate?") is True
