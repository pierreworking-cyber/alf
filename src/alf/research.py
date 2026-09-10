"""
External research for ALF.

This module retrieves web pages, extracts readable text, and selects
relevant evidence for answer generation.
"""

from html.parser import HTMLParser
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

import trafilatura
from rank_bm25 import BM25Okapi

from .llm import generate_json

MAX_SEARCH_RESULTS = 10
MAX_EVIDENCE_RESULTS = 10
PASSAGE_MAX_WORDS = 120


class ResultParser(HTMLParser):
    """Parse DuckDuckGo HTML search results."""

    def __init__(self):
        super().__init__()
        self.results = []
        self.in_result = False
        self.in_title = False
        self.current = {}

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        classes = (attributes.get("class") or "").split()

        if tag == "div" and "result" in classes:
            self.in_result = True
            self.current = {}

        elif self.in_result and tag == "a" and "result__a" in classes:
            self.in_title = True
            self.current["url"] = attributes.get("href", "")

    def handle_endtag(self, tag):
        if tag == "a":
            self.in_title = False

        elif tag == "div" and self.in_result:
            if self.current.get("title") and self.current.get("url"):
                self.results.append(self.current)
            self.in_result = False

    def handle_data(self, data):
        if self.in_title:
            self.current["title"] = (
                self.current.get("title", "") + data
            ).strip()


def domain(url):
    """Return the normalised domain name for a URL."""

    return urlparse(url).netloc.lower().removeprefix("www.")


def search_web(question):
    """Search DuckDuckGo and return candidate result URLs."""

    data = urlencode({"q": question}).encode("utf-8")

    request = Request(
        "https://html.duckduckgo.com/html/",
        data=data,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/139.0 Safari/537.36"
            ),
            "Referer": "https://html.duckduckgo.com/",
        },
        method="POST",
    )

    with urlopen(request, timeout=15) as response:
        html = response.read()

    parser = ResultParser()
    parser.feed(html.decode("utf-8", errors="replace"))

    return parser.results[:MAX_SEARCH_RESULTS]


def fetch_and_extract(url):
    """Fetch a web page and extract its readable text."""

    request = Request(
        url,
        headers={
            "User-Agent": "ALF-Mac-research/0.1",
        },
    )

    with urlopen(request, timeout=15) as response:
        html = response.read()

    text = trafilatura.extract(
        html,
        url=url,
        favor_precision=True,
    )

    return text or ""


def split_into_passages(text, max_words=PASSAGE_MAX_WORDS):
    """Split extracted text into bounded passages."""

    words = text.split()
    passages = []

    for start in range(0, len(words), max_words):
        passage = " ".join(words[start:start + max_words])

        if passage:
            passages.append(passage)

    return passages


def build_documents(results):
    """Fetch and extract readable text from search results."""

    documents = []

    for result in results:
        try:
            text = fetch_and_extract(result["url"])
        except Exception:
            continue

        if not text:
            continue

        documents.append(
            {
                "title": result["title"],
                "url": result["url"],
                "domain": domain(result["url"]),
                "passages": split_into_passages(text),
            }
        )

    return documents


def rank_passages(question, documents):
    """Rank extracted passages by lexical relevance to the question."""

    passages = []

    for document in documents:
        for passage in document["passages"]:
            passages.append(
                {
                    "title": document["title"],
                    "url": document["url"],
                    "domain": document["domain"],
                    "text": passage,
                }
            )

    if not passages:
        return []

    tokenized = [
        passage["text"].lower().split()
        for passage in passages
    ]

    bm25 = BM25Okapi(tokenized)

    scores = bm25.get_scores(
        question.lower().split()
    )

    ranked = sorted(
        zip(scores, passages),
        key=lambda item: item[0],
        reverse=True,
    )

    return [
        {
            **passage,
            "score": score,
        }
        for score, passage in ranked[:MAX_EVIDENCE_RESULTS]
    ]


def build_source_diverse_pool(documents, ranked_passages):
    """Keep the strongest evidence from as many sources as possible."""

    selected = []
    seen_domains = set()

    for candidate in ranked_passages:
        if candidate["domain"] in seen_domains:
            continue

        selected.append(candidate)
        seen_domains.add(candidate["domain"])

    for document in documents:
        if document["domain"] in seen_domains:
            continue

        if not document["passages"]:
            continue

        selected.append(
            {
                "title": document["title"],
                "url": document["url"],
                "domain": document["domain"],
                "text": document["passages"][0],
                "score": 0.0,
            }
        )
        seen_domains.add(document["domain"])

    return selected


def research(question):
    """Retrieve and rank web evidence for a question."""

    results = search_web(question)
    documents = build_documents(results)

    ranked_passages = rank_passages(
        question,
        documents,
    )

    return build_source_diverse_pool(
        documents,
        ranked_passages,
    )


def evaluate_evidence(question, candidates):
    """Judge retrieved evidence and identify the best-supported answer."""

    evidence = "\n\n".join(
        f"Candidate {index}\n"
        f"Source: {candidate['domain']}\n"
        f"Title: {candidate['title']}\n"
        f"URL: {candidate['url']}\n"
        f"Evidence: {candidate['text']}"
        for index, candidate in enumerate(candidates, start=1)
    )

    prompt = f"""
You are the research evidence judge for ALF.

The user asked:

{question}

The following web evidence was retrieved:

{evidence}

Determine the best-supported answer using ONLY the supplied evidence.

Your job has two stages:

1. Relevance:
   Identify candidates that actually contain evidence relevant to
   the question.

2. Conflict resolution:
   If relevant candidates disagree, determine which claim is best
   supported.

Rules:

- Do not use your own general knowledge.
- Do not invent missing facts.
- Prefer authoritative sources over less authoritative sources.
- Prefer primary or official sources where appropriate.
- Prefer explicit dates over vague or undated claims.
- Pay attention to whether a claim is stale.
- A source can be relevant but still be outdated.
- Do not simply count how many sources make a claim.
- If the evidence genuinely cannot resolve the question, say so.

Return JSON only:

{{
    "answer": "best-supported answer",
    "confidence": "high|medium|low",
    "supporting_candidates": [1, 2],
    "rejected_candidates": [3],
    "reason": "brief explanation"
}}
"""
    return generate_json(prompt)


def select_evidence(candidates, evaluation):
    """Return the evidence candidates selected by the research judge."""

    selected = []

    for index in evaluation["supporting_candidates"]:
        selected.append(candidates[index - 1])

    return selected

