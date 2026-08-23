"""
Fresh-information research for ALF.

Provides a small boundary between ALF and external information sources.
"""

import json
from urllib.parse import quote
from urllib.request import Request, urlopen

from .identity import get_identity

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"

MAX_WEB_RESULTS = 3


def fetch(url):
    """
    Fetch text content from an external URL.
    """
    identity = get_identity()

    request = Request(
        url,
        headers={"User-Agent": f"{identity['name']}/{identity['version']}/research"},
    )

    with urlopen(request, timeout=10) as response:
        return response.read().decode("utf-8")


def search_wikipedia(question):
    """
    Search Wikipedia for a question and return candidate pages.
    """
    params = (
        "?action=query"
        "&list=search"
        "&format=json"
        "&utf8=1"
        "&srlimit=5"
        f"&srsearch={quote(question)}"
    )

    data = json.loads(fetch(WIKIPEDIA_API + params))

    return [
        {
            "title": result["title"],
            "page_id": result["pageid"],
        }
        for result in data["query"]["search"]
    ]


def fetch_wikipedia_page(page_id):
    """
    Fetch a concise extract from a Wikipedia page by page ID.
    """
    url = (
        "https://en.wikipedia.org/w/api.php"
        f"?action=query"
        f"&prop=extracts"
        f"&explaintext=1"
        f"&exintro=1"
        f"&format=json"
        f"&pageids={page_id}"
    )

    data = json.loads(fetch(url))
    page = data["query"]["pages"][str(page_id)]

    return page.get("extract", "")


def research_wikipedia_candidates(question):
    """
    Search Wikipedia and return a small evidence set for evaluation.
    """

    results = search_wikipedia(question)

    candidates = []

    for result in results[:3]:
        text = fetch_wikipedia_page(result["page_id"])

        if not text:
            continue

        candidates.append(
            {
                "source": "wikipedia",
                "title": result["title"],
                "page_id": result["page_id"],
                "text": text[:1500],
            }
        )

    return candidates


def search_web(question):
    """
    Search SearXNG and return a small set of candidate pages.
    """
    url = f"http://127.0.0.1:8080/search?q={quote(question)}&format=json"

    data = json.loads(fetch(url))

    results = []

    for result in data.get("results", [])[:MAX_WEB_RESULTS]:
        title = result.get("title")
        text = result.get("content", "")
        result_url = result.get("url")

        if not title or not result_url:
            continue

        results.append(
            {
                "source": "web",
                "title": title,
                "url": result_url,
                "text": text,
            }
        )

    return results


def research_web(question):
    """
    Search the web and return a small evidence set for evaluation.
    """

    results = search_web(question)

    candidates = []

    for result in results:
        text = result.get("text", "")

        if not text:
            continue

        candidates.append(
            {
                "source": "web",
                "title": result["title"],
                "url": result["url"],
                "text": text,
            }
        )

    return candidates


