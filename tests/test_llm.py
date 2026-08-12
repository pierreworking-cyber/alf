import json

from alf import llm


def test_check_ollama_when_service_and_model_are_available(monkeypatch):
    response_data = {
        "models": [
            {"name": "qwen3:4b"},
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
        "model": "qwen3:4b",
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
        "model": "qwen3:4b",
        "error": None,
    }


def test_check_ollama_when_service_is_unavailable(monkeypatch):
    def fake_urlopen(request, timeout):
        raise OSError("Connection refused")

    monkeypatch.setattr(llm, "urlopen", fake_urlopen)

    result = llm.check_ollama()

    assert result["available"] is False
    assert result["model_available"] is False
    assert result["model"] == "qwen3:4b"
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

    def fake_urlopen(request):
        return FakeResponse()

    monkeypatch.setattr(llm, "urlopen", fake_urlopen)

    result = llm.ask(
        "What is the capital of France?",
        {
            "source": "wikipedia",
            "title": "France",
            "page_id": 123,
            "text": "France is a country in Europe.",
        },
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

    def fake_urlopen(request):
        return FakeResponse()

    monkeypatch.setattr(llm, "urlopen", fake_urlopen)

    result = llm.ask("What is 2 + 2?", None)

    assert result == "An answer without research."


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

    def fake_urlopen(request):
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

    def fake_urlopen(request):
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

    def fake_urlopen(request):
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
