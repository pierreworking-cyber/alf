import json

from alf import research


def test_extract_text_returns_extracted_text(monkeypatch):
    monkeypatch.setattr(
        research.trafilatura,
        "extract",
        lambda html: "Extracted article text.",
    )

    assert research.extract_text("<html>ignored</html>") == "Extracted article text."


def test_extract_text_returns_empty_string_when_extraction_fails(monkeypatch):
    monkeypatch.setattr(
        research.trafilatura,
        "extract",
        lambda html: None,
    )

    assert research.extract_text("<html>ignored</html>") == ""


def test_search_wikipedia_parses_results(monkeypatch):
    response = json.dumps(
        {
            "query": {
                "search": [
                    {
                        "title": "Tunisia",
                        "pageid": 123,
                    },
                    {
                        "title": "Tunis",
                        "pageid": 456,
                    },
                ]
            }
        }
    )

    monkeypatch.setattr(research, "fetch", lambda url: response)

    results = research.search_wikipedia("What is the capital of Tunisia?")

    assert results == [
        {
            "title": "Tunisia",
            "page_id": 123,
        },
        {
            "title": "Tunis",
            "page_id": 456,
        },
    ]


def test_fetch_wikipedia_page_returns_extract(monkeypatch):
    response = json.dumps(
        {
            "query": {
                "pages": {
                    "123": {
                        "extract": "Tunisia is a country in North Africa.",
                    }
                }
            }
        }
    )

    monkeypatch.setattr(research, "fetch", lambda url: response)

    assert (
        research.fetch_wikipedia_page(123)
        == "Tunisia is a country in North Africa."
    )


def test_research_wikipedia_returns_first_result(monkeypatch):
    monkeypatch.setattr(
        research,
        "search_wikipedia",
        lambda question: [
            {
                "title": "Tunisia",
                "page_id": 123,
            },
            {
                "title": "Tunis",
                "page_id": 456,
            },
        ],
    )

    monkeypatch.setattr(
        research,
        "fetch_wikipedia_page",
        lambda page_id: "Tunisia is a country in North Africa.",
    )

    result = research.research_wikipedia("What is Tunisia?")

    assert result == {
        "source": "wikipedia",
        "title": "Tunisia",
        "page_id": 123,
        "text": "Tunisia is a country in North Africa.",
    }


def test_research_wikipedia_returns_none_when_no_results(monkeypatch):
    monkeypatch.setattr(
        research,
        "search_wikipedia",
        lambda question: [],
    )

    assert research.research_wikipedia("Something unknown") is None


def test_research_wikipedia_limits_text_length(monkeypatch):
    long_text = "A" * (research.MAX_RESEARCH_CHARS + 100)

    monkeypatch.setattr(
        research,
        "search_wikipedia",
        lambda question: [
            {
                "title": "Test",
                "page_id": 123,
            }
        ],
    )

    monkeypatch.setattr(
        research,
        "fetch_wikipedia_page",
        lambda page_id: long_text,
    )

    result = research.research_wikipedia("Test")

    assert len(result["text"]) == research.MAX_RESEARCH_CHARS
