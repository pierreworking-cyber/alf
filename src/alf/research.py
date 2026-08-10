"""
Fresh-information research for ALF.

Provides a small boundary between ALF and external information sources.
"""

import json
from urllib.parse import quote
from urllib.request import Request, urlopen

import trafilatura

from .identity import get_identity

WIKIPEDIA_API = (
    "https://en.wikipedia.org/w/api.php"
)

MAX_RESEARCH_CHARS = 6000

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
