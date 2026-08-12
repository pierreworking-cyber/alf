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


def test_search_web_returns_candidate_results(monkeypatch):
    html = """
    <html>
        <body>
            <div class="result">
                <a class="result__a" href="https://example.com/first">
                    First result
                </a>
            </div>
            <div class="result">
                <a class="result__a" href="https://example.com/second">
                    Second result
                </a>
            </div>
        </body>
    </html>
    """

    monkeypatch.setattr(
        research,
        "fetch",
        lambda url: html,
    )

    result = research.search_web("test question")

    assert result == [
        {
            "source": "web",
            "title": "First result",
            "url": "https://example.com/first",
        },
        {
            "source": "web",
            "title": "Second result",
            "url": "https://example.com/second",
        },
    ]


def test_search_web_limits_results(monkeypatch):
    html = """
    <html>
        <body>
            <div class="result">
                <a class="result__a" href="https://example.com/1">One</a>
            </div>
            <div class="result">
                <a class="result__a" href="https://example.com/2">Two</a>
            </div>
            <div class="result">
                <a class="result__a" href="https://example.com/3">Three</a>
            </div>
            <div class="result">
                <a class="result__a" href="https://example.com/4">Four</a>
            </div>
        </body>
    </html>
    """

    monkeypatch.setattr(
        research,
        "fetch",
        lambda url: html,
    )

    result = research.search_web("test question")

    assert len(result) == research.MAX_WEB_RESULTS


def test_search_web_skips_results_without_links(monkeypatch):
    html = """
    <html>
        <body>
            <div class="result">
                <span>No link here</span>
            </div>
            <div class="result">
                <a class="result__a" href="https://example.com/useful">
                    Useful result
                </a>
            </div>
        </body>
    </html>
    """

    monkeypatch.setattr(
        research,
        "fetch",
        lambda url: html,
    )

    result = research.search_web("test question")

    assert result == [
        {
            "source": "web",
            "title": "Useful result",
            "url": "https://example.com/useful",
        }
    ]


def test_research_web_returns_page_evidence(monkeypatch):
    monkeypatch.setattr(
        research,
        "search_web",
        lambda question: [
            {
                "source": "web",
                "title": "First result",
                "url": "https://example.com/first",
            },
            {
                "source": "web",
                "title": "Second result",
                "url": "https://example.com/second",
            },
        ],
    )

    monkeypatch.setattr(
        research,
        "fetch",
        lambda url: f"<html><body>Article for {url}</body></html>",
    )

    monkeypatch.setattr(
        research.trafilatura,
        "extract",
        lambda html: html.replace("<html><body>", "").replace(
            "</body></html>", ""
        ),
    )

    result = research.research_web("test question")

    assert result == [
        {
            "source": "web",
            "title": "First result",
            "url": "https://example.com/first",
            "text": "Article for https://example.com/first",
        },
        {
            "source": "web",
            "title": "Second result",
            "url": "https://example.com/second",
            "text": "Article for https://example.com/second",
        },
    ]


def test_research_web_limits_page_text(monkeypatch):
    long_text = "A" * 2000

    monkeypatch.setattr(
        research,
        "search_web",
        lambda question: [
            {
                "source": "web",
                "title": "Test",
                "url": "https://example.com/test",
            }
        ],
    )

    monkeypatch.setattr(
        research,
        "fetch",
        lambda url: "<html></html>",
    )

    monkeypatch.setattr(
        research.trafilatura,
        "extract",
        lambda html: long_text,
    )

    result = research.research_web("test question")

    assert len(result) == 1
    assert len(result[0]["text"]) == research.MAX_WEB_PAGE_CHARS


def test_research_web_skips_failed_pages(monkeypatch):
    monkeypatch.setattr(
        research,
        "search_web",
        lambda question: [
            {
                "source": "web",
                "title": "Broken",
                "url": "https://example.com/broken",
            },
            {
                "source": "web",
                "title": "Useful",
                "url": "https://example.com/useful",
            },
        ],
    )

    def fake_fetch(url):
        if url.endswith("broken"):
            raise OSError("Connection failed")

        return "<html><body>Useful article.</body></html>"

    monkeypatch.setattr(
        research,
        "fetch",
        fake_fetch,
    )

    monkeypatch.setattr(
        research.trafilatura,
        "extract",
        lambda html: "Useful article.",
    )

    result = research.research_web("test question")

    assert result == [
        {
            "source": "web",
            "title": "Useful",
            "url": "https://example.com/useful",
            "text": "Useful article.",
        }
    ]


def test_search_web_returns_empty_list_when_no_results(monkeypatch):
    html = """
    <html>
        <body>
            <div class="results"></div>
        </body>
    </html>
    """

    monkeypatch.setattr(
        research,
        "fetch",
        lambda url: html,
    )

    result = research.search_web("something unknown")

    assert result == []


def test_search_web_parses_results(monkeypatch):
    html = """
    <html>
        <body>
            <div class="result">
                <a class="result__a" href="https://example.com/film">
                    Example Film
                </a>
            </div>
            <div class="result">
                <a class="result__a" href="https://example.com/article">
                    Example Article
                </a>
            </div>
        </body>
    </html>
    """

    monkeypatch.setattr(
        research,
        "fetch",
        lambda url: html,
    )

    result = research.search_web("example film")

    assert result == [
        {
            "source": "web",
            "title": "Example Film",
            "url": "https://example.com/film",
        },
        {
            "source": "web",
            "title": "Example Article",
            "url": "https://example.com/article",
        },
    ]


def test_search_web_limits_number_of_results(monkeypatch):
    results = "".join(
        f"""
        <div class="result">
            <a class="result__a" href="https://example.com/{index}">
                Result {index}
            </a>
        </div>
        """
        for index in range(5)
    )

    monkeypatch.setattr(
        research,
        "fetch",
        lambda url: f"<html><body>{results}</body></html>",
    )

    result = research.search_web("example")

    assert len(result) == research.MAX_WEB_RESULTS
