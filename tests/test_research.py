import json

from alf import research


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


def test_research_wikipedia_candidates_returns_multiple_results(monkeypatch):
    monkeypatch.setattr(
        research,
        "search_wikipedia",
        lambda question: [
            {
                "title": "First",
                "page_id": 123,
            },
            {
                "title": "Second",
                "page_id": 456,
            },
            {
                "title": "Third",
                "page_id": 789,
            },
            {
                "title": "Fourth",
                "page_id": 999,
            },
        ],
    )

    monkeypatch.setattr(
        research,
        "fetch_wikipedia_page",
        lambda page_id: f"Article text for {page_id}.",
    )

    result = research.research_wikipedia_candidates("Test question")

    assert result == [
        {
            "source": "wikipedia",
            "title": "First",
            "page_id": 123,
            "text": "Article text for 123.",
        },
        {
            "source": "wikipedia",
            "title": "Second",
            "page_id": 456,
            "text": "Article text for 456.",
        },
        {
            "source": "wikipedia",
            "title": "Third",
            "page_id": 789,
            "text": "Article text for 789.",
        },
    ]


def test_research_wikipedia_candidates_limits_text_length(monkeypatch):
    long_text = "A" * 2000

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

    result = research.research_wikipedia_candidates("Test")

    assert len(result) == 1
    assert len(result[0]["text"]) == 1500


def test_research_wikipedia_candidates_skips_empty_articles(monkeypatch):
    monkeypatch.setattr(
        research,
        "search_wikipedia",
        lambda question: [
            {
                "title": "Empty",
                "page_id": 123,
            },
            {
                "title": "Useful",
                "page_id": 456,
            },
        ],
    )

    monkeypatch.setattr(
        research,
        "fetch_wikipedia_page",
        lambda page_id: "" if page_id == 123 else "Useful article.",
    )

    result = research.research_wikipedia_candidates("Test")

    assert result == [
        {
            "source": "wikipedia",
            "title": "Useful",
            "page_id": 456,
            "text": "Useful article.",
        }
    ]


def test_search_web_returns_empty_list_when_no_results(monkeypatch):
    response = json.dumps({"results": []})

    monkeypatch.setattr(
        research,
        "fetch",
        lambda url: response,
    )

    result = research.search_web("something unknown")

    assert result == []
