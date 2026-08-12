"""
Fresh-information research for ALF.

Provides a small boundary between ALF and external information sources.
"""

import json
from urllib.parse import quote
from urllib.request import Request, urlopen

import trafilatura
from bs4 import BeautifulSoup

from .identity import get_identity

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"

MAX_RESEARCH_CHARS = 6000
WEB_SEARCH_URL = "https://html.duckduckgo.com/html/"
MAX_WEB_RESULTS = 3
MAX_WEB_PAGE_CHARS = 1500


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


def extract_text(html):
    """
    Extract readable text from HTML content.
    """
    text = trafilatura.extract(html)

    return text or ""


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


def research_wikipedia(question):
    """
    Search Wikipedia and return the first relevant page as a research source.
    """

    results = search_wikipedia(question)

    if not results:
        return None

    result = results[0]

    return {
        "source": "wikipedia",
        "title": result["title"],
        "page_id": result["page_id"],
        "text": fetch_wikipedia_page(result["page_id"])[:MAX_RESEARCH_CHARS],
    }


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
    Search the web and return a small set of candidate pages.
    """

    html = fetch(f"{WEB_SEARCH_URL}?q={quote(question)}")

    soup = BeautifulSoup(html, "html.parser")

    results = []

    for result in soup.select(".result")[:MAX_WEB_RESULTS]:
        link = result.select_one(".result__a")

        if link is None:
            continue

        href = link.get("href")

        if not href:
            continue

        results.append(
            {
                "source": "web",
                "title": link.get_text(" ", strip=True),
                "url": href,
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
        try:
            html = fetch(result["url"])
        except Exception:
            continue

        text = extract_text(html)

        if not text:
            continue

        candidates.append(
            {
                "source": "web",
                "title": result["title"],
                "url": result["url"],
                "text": text[:MAX_WEB_PAGE_CHARS],
            }
        )

    return candidates


