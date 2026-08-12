from alf.classifier import classify
from alf.router import Route


def test_classify_system_question(monkeypatch):
    monkeypatch.setattr(
        "alf.classifier.llm._generate",
        lambda prompt: "system",
    )

    assert classify("What operating system am I running?") == Route.SYSTEM


def test_classify_memory_question(monkeypatch):
    monkeypatch.setattr(
        "alf.classifier.llm._generate",
        lambda prompt: "memory",
    )

    assert classify("What did we decide about SearXNG?") == Route.MEMORY


def test_classify_research_question(monkeypatch):
    monkeypatch.setattr(
        "alf.classifier.llm._generate",
        lambda prompt: "research",
    )

    assert classify("What is the latest version of Python?") == Route.RESEARCH


def test_classify_general_knowledge_question(monkeypatch):
    monkeypatch.setattr(
        "alf.classifier.llm._generate",
        lambda prompt: "llm",
    )

    assert classify("What does pytest -q mean?") == Route.LLM


def test_classify_unsupported_question(monkeypatch):
    monkeypatch.setattr(
        "alf.classifier.llm._generate",
        lambda prompt: "decline",
    )

    assert classify("Can ALF make me a cup of tea?") == Route.DECLINE
