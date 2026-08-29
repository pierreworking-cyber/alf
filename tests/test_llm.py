import json

from alf import llm


def test_check_ollama_when_service_and_model_are_available(monkeypatch):
    response_data = {
        "models": [
            {"name": "qwen3:8b"},
            {"name": "some-other-model"},
        ],
    }

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            pass

        def read(self):
            return json.dumps(response_data).encode("utf-8")

    monkeypatch.setattr(
        llm,
        "urlopen",
        lambda request, timeout: FakeResponse(),
    )

    result = llm.check_ollama()

    assert result == {
        "available": True,
        "model_available": True,
        "model": "qwen3:8b",
        "error": None,
    }


def test_check_ollama_when_model_is_missing(monkeypatch):
    response_data = {
        "models": [
            {"name": "some-other-model"},
        ],
    }

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            pass

        def read(self):
            return json.dumps(response_data).encode("utf-8")

    monkeypatch.setattr(
        llm,
        "urlopen",
        lambda request, timeout: FakeResponse(),
    )

    result = llm.check_ollama()

    assert result == {
        "available": True,
        "model_available": False,
        "model": "qwen3:8b",
        "error": None,
    }


def test_check_ollama_when_service_is_unavailable(monkeypatch):
    def fake_urlopen(request, timeout):
        raise OSError("Connection refused")

    monkeypatch.setattr(llm, "urlopen", fake_urlopen)

    result = llm.check_ollama()

    assert result["available"] is False
    assert result["model_available"] is False
    assert result["model"] == "qwen3:8b"
    assert result["error"] == "Connection refused"


def test_ask_returns_ollama_response(monkeypatch):
    response_data = {
        "response": "The answer from Ollama.",
    }

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            pass

        def read(self):
            return json.dumps(response_data).encode("utf-8")

    def fake_urlopen(request, timeout):
        return FakeResponse()

    monkeypatch.setattr(llm, "urlopen", fake_urlopen)

    result = llm.ask(
        {
            "question": "What is the capital of France?",
            "evidence": [
                {
                    "source": "wikipedia",
                    "title": "France",
                    "page_id": 123,
                    "text": "France is a country in Europe.",
                }
            ],
        }
    )

    assert result == "The answer from Ollama."


def test_ask_handles_no_research(monkeypatch):
    response_data = {
        "response": "An answer without research.",
    }

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            pass

        def read(self):
            return json.dumps(response_data).encode("utf-8")

    def fake_urlopen(request, timeout):
        return FakeResponse()

    monkeypatch.setattr(llm, "urlopen", fake_urlopen)

    result = llm.ask(
        {
            "question": "What is 2 + 2?",
            "evidence": [],
        }
    )

    assert result == "An answer without research."


def test_ask_requires_answers_to_stay_within_evidence(monkeypatch):
    captured = {}

    def fake_generate(prompt):
        captured["prompt"] = prompt
        return "I don't have enough evidence to answer that."

    monkeypatch.setattr(
        llm,
        "generate",
        fake_generate,
    )

    result = llm.ask(
        {
            "question": "What did we decide about penguin mating habits?",
            "evidence": [
                {
                    "source": "memory",
                    "content": "ALF should use evidence rather than guesses.",
                }
            ],
        }
    )

    assert (
        "Answer using only the supplied evidence."
        in captured["prompt"]
    )
    assert (
        "Do not use your own general knowledge to fill gaps."
        in captured["prompt"]
    )
    assert result == "I don't have enough evidence to answer that."


def test_ask_uses_detailed_style_when_verbose(monkeypatch):
    captured = {}

    def fake_generate(prompt):
        captured["prompt"] = prompt
        return "A detailed answer."

    monkeypatch.setattr(
        llm,
        "generate",
        fake_generate,
    )

    result = llm.ask(
        {
            "question": "What are microbes?",
            "evidence": [],
            "verbose": True,
        }
    )

    assert "Give a detailed, well-developed answer." in captured["prompt"]
    assert (
        "Provide useful context and explanation rather than a brief response."
        in captured["prompt"]
    )
    assert result == "A detailed answer."


def test_ask_uses_concise_style_when_not_verbose(monkeypatch):
    captured = {}

    def fake_generate(prompt):
        captured["prompt"] = prompt
        return "A concise answer."

    monkeypatch.setattr(
        llm,
        "generate",
        fake_generate,
    )

    result = llm.ask(
        {
            "question": "What are microbes?",
            "evidence": [],
            "verbose": False,
        }
    )

    assert "Give a concise but useful answer." in captured["prompt"]
    assert "Do not add unnecessary detail." in captured["prompt"]
    assert result == "A concise answer."


def test_evaluate_research_returns_relevant_result(monkeypatch):
    response_data = {
        "response": json.dumps(
            {
                "relevant": True,
                "candidates": [1],
                "reason": "The article directly describes the subject in the question.",
            }
        )
    }

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            pass

        def read(self):
            return json.dumps(response_data).encode("utf-8")

    def fake_urlopen(request, timeout):
        return FakeResponse()

    monkeypatch.setattr(llm, "urlopen", fake_urlopen)

    result = llm.evaluate_research(
        "What is the capital of France?",
        [
            {
                "source": "wikipedia",
                "title": "France",
                "page_id": 123,
                "text": "France is a country in Europe. Its capital is Paris.",
            }
        ],
    )

    assert result == {
        "relevant": True,
        "candidates": [1],
        "reason": "The article directly describes the subject in the question.",
    }


def test_evaluate_research_returns_not_relevant_result(monkeypatch):
    response_data = {
        "response": json.dumps(
            {
                "relevant": False,
                "candidates": [],
                "reason": "The supplied articles do not match the question.",
            }
        )
    }

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            pass

        def read(self):
            return json.dumps(response_data).encode("utf-8")

    def fake_urlopen(request, timeout):
        return FakeResponse()

    monkeypatch.setattr(llm, "urlopen", fake_urlopen)

    result = llm.evaluate_research(
        "What film featured children mistaking a homeless man for Jesus?",
        [
            {
                "source": "wikipedia",
                "title": "Whitney Houston",
                "page_id": 34071,
                "text": "Whitney Houston was an American singer and actress.",
            }
        ],
    )

    assert result == {
        "relevant": False,
        "candidates": [],
        "reason": "The supplied articles do not match the question.",
    }


def test_evaluate_research_rejects_invalid_response(monkeypatch):
    response_data = {
        "response": "This is not JSON.",
    }

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            pass

        def read(self):
            return json.dumps(response_data).encode("utf-8")

    def fake_urlopen(request, timeout):
        return FakeResponse()

    monkeypatch.setattr(llm, "urlopen", fake_urlopen)

    try:
        llm.evaluate_research(
            "What is the capital of France?",
            [
                {
                    "source": "wikipedia",
                    "title": "France",
                    "page_id": 123,
                    "text": "France is a country in Europe.",
                }
            ],
        )
    except ValueError as error:
        assert str(error) == "Invalid research evaluation response"
    else:
        raise AssertionError("Expected ValueError")


def make_news_synthesis_item(**overrides):
    """
    Build a news item dict for synthesis tests.
    """

    item = {
        "id": 1,
        "subject": "Ukraine",
        "feed_title": "https://feeds.example/ukraine.rss",
        "title": "Ukraine economy shows strong growth",
        "url": "https://feeds.example/n/1",
        "summary": "The economy grew strongly last month.",
        "published_at": "2026-08-27T10:00:00Z",
    }

    item.update(overrides)

    return item


def test_synthesize_news_builds_numbered_evidence(monkeypatch):
    captured = {}

    items = [
        make_news_synthesis_item(),
        make_news_synthesis_item(
            id=2,
            title="Ukraine plans a redesign",
            url="https://feeds.example/n/2",
            summary="",
        ),
    ]

    def fake_generate(prompt):
        captured["prompt"] = prompt
        return "Ukraine's economy grew strongly last week [1]."

    monkeypatch.setattr(llm, "generate", fake_generate)

    result = llm.synthesize_news(
        "What has happened in Ukraine recently?",
        items,
    )

    assert result == "Ukraine's economy grew strongly last week [1]."

    prompt = captured["prompt"]

    assert "What has happened in Ukraine recently?" in prompt
    assert "[1] Ukraine economy shows strong growth" in prompt
    assert "Ukraine, 27-Aug-2026 10:00, Example" in prompt
    assert "https://feeds.example/n/1" in prompt
    assert "Summary: The economy grew strongly last month." in prompt
    assert "[2] Ukraine plans a redesign" in prompt
    assert prompt.count("Summary:") == 1


def test_synthesize_news_grounds_the_model_to_supplied_evidence(monkeypatch):
    captured = {}

    def fake_generate(prompt):
        captured["prompt"] = prompt
        return "First story [1]."

    monkeypatch.setattr(llm, "generate", fake_generate)

    items = [
        make_news_synthesis_item(),
        make_news_synthesis_item(
            id=2,
            title="Second story",
            url="https://feeds.example/n/2",
            summary="The second story continues.",
        ),
    ]

    llm.synthesize_news(
        "What has happened in Ukraine recently?",
        items,
    )

    prompt = captured["prompt"]

    assert "the ONLY evidence you may use" in prompt
    assert "Do not invent facts or sources" in prompt
    assert "rely only on its title" in prompt
    assert "Answer as a news update of what the supplied articles say" in prompt
    assert "not as general or encyclopedic knowledge" in prompt
    assert "conflict or report differently, say so" in prompt
    assert "Distinguish reported claims from established facts" in prompt
    assert "only where those articles support the claim" in prompt
    assert "do not cover the user's question, say so" in prompt
    assert "plainly rather than guessing" in prompt
    assert "https://feeds.example/n/1" in prompt
    assert "https://feeds.example/n/2" in prompt
    assert "https://feeds.example/n/3" not in prompt


def test_synthesize_news_omits_summary_when_missing(monkeypatch):
    captured = {}

    def fake_generate(prompt):
        captured["prompt"] = prompt
        return "ok"

    monkeypatch.setattr(llm, "generate", fake_generate)

    items = [
        make_news_synthesis_item(summary=""),
        make_news_synthesis_item(id=2, title="No summary item", summary=None),
    ]

    llm.synthesize_news("Question?", items)

    assert "Summary:" not in captured["prompt"]


def test_synthesize_news_caps_evidence_items(monkeypatch):
    captured = {}

    def fake_generate(prompt):
        captured["prompt"] = prompt
        return "ok"

    monkeypatch.setattr(llm, "generate", fake_generate)

    items = [
        make_news_synthesis_item(
            id=index,
            title=f"Story {index}",
            url=f"https://feeds.example/n/{index}",
        )
        for index in range(1, 21)
    ]

    llm.synthesize_news("Question?", items)

    prompt = captured["prompt"]

    assert "[1] Story 1" in prompt
    assert "[15] Story 15" in prompt
    assert "[16] Story 16" not in prompt


def test_synthesize_news_uses_fuller_style_when_verbose(monkeypatch):
    captured = {}

    def fake_generate(prompt):
        captured["prompt"] = prompt
        return "ok"

    monkeypatch.setattr(llm, "generate", fake_generate)

    llm.synthesize_news(
        "Question?",
        [make_news_synthesis_item()],
        verbose=True,
    )

    assert "Give a slightly fuller update than usual" in captured["prompt"]
    assert "Keep the update concise." not in captured["prompt"]


def test_synthesize_news_uses_concise_style_by_default(monkeypatch):
    captured = {}

    def fake_generate(prompt):
        captured["prompt"] = prompt
        return "ok"

    monkeypatch.setattr(llm, "generate", fake_generate)

    llm.synthesize_news("Question?", [make_news_synthesis_item()])

    assert "Keep the update concise." in captured["prompt"]
