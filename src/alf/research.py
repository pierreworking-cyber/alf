"""
External research for ALF.

This module retrieves web pages, extracts readable text, and selects
relevant evidence for answer generation.
"""

import re
import time
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from rank_bm25 import BM25Okapi
import trafilatura

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

    text = html.decode("utf-8", errors="replace")

    if "Unfortunately, bots use DuckDuckGo too." in text:
        print(
            "[research] DuckDuckGo has presented a bot challenge. "
            "Please open DuckDuckGo in a browser and perform a normal "
            "search, then try ALF again.",
            flush=True,
        )
        return []

    parser = ResultParser()
    parser.feed(text)

    results = []

    for result in parser.results:
        result_url = result["url"]

        if domain(result_url) == "duckduckgo.com":
            continue

        results.append(result)

    return results[:MAX_SEARCH_RESULTS]


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

    def fetch_result(result):
        url = result["url"]

        try:
            text = fetch_and_extract(url)
        except Exception:
            return None

        if not text:
            return None

        return {
            "title": result["title"],
            "url": url,
            "domain": domain(url),
            "passages": split_into_passages(text),
        }

    with ThreadPoolExecutor(max_workers=5) as executor:
        documents = list(
            executor.map(fetch_result, results)
        )

    return [
        document
        for document in documents
        if document is not None
    ]


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

    def tokenize(text):
        return re.findall(r"\b\w+\b", text.lower())

    tokenized = [
        tokenize(passage["text"])
        for passage in passages
    ]

    bm25 = BM25Okapi(tokenized)

    query_tokens = tokenize(question)

    scores = bm25.get_scores(query_tokens)

    ranked_scores = []

    for score, passage, tokens in zip(
        scores,
        passages,
        tokenized,
    ):
        overlap = len(set(query_tokens) & set(tokens))

        adjusted_score = max(
            0.0,
            float(score) + overlap * 0.1,
        )

        ranked_scores.append(
            (
                adjusted_score,
                passage,
            )
        )

    ranked = sorted(
        ranked_scores,
        key=lambda item: item[0],
        reverse=True,
    )

    return [
        {
            **passage,
            "score": float(score),
        }
        for score, passage in ranked
    ]


def build_source_diverse_pool(documents, ranked_passages):
    """Keep relevant evidence from diverse and authoritative sources."""

    selected = []
    seen_domains = set()

    authoritative_domains = {
        "gov.uk",
    }

    # First protect authoritative sources from being crowded out
    # by slightly higher-scoring general sources.
    for candidate in ranked_passages:
        if candidate["score"] <= 0:
            continue

        if candidate["domain"] not in authoritative_domains:
            continue

        if candidate["domain"] in seen_domains:
            continue

        selected.append(candidate)
        seen_domains.add(candidate["domain"])

    # Then fill the remaining evidence slots by relevance,
    # keeping the sources diverse.
    for candidate in ranked_passages:
        if len(selected) >= MAX_EVIDENCE_RESULTS:
            break

        if candidate["score"] <= 0:
            continue

        if candidate["domain"] in seen_domains:
            continue

        selected.append(candidate)
        seen_domains.add(candidate["domain"])

    return selected


def research(question, timings=None):
    """Retrieve and rank web evidence for a question."""

    if timings is None:
        timings = {}

    start = time.perf_counter()
    results = search_web(question)
    timings["search"] = time.perf_counter() - start

    start = time.perf_counter()
    documents = build_documents(results)
    timings["fetch_extract"] = time.perf_counter() - start

    start = time.perf_counter()
    ranked_passages = rank_passages(
        question,
        documents,
    )
    timings["ranking"] = time.perf_counter() - start

    start = time.perf_counter()
    selected = build_source_diverse_pool(
        documents,
        ranked_passages,
    )
    timings["diversity"] = time.perf_counter() - start

    return selected


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

Your job has three stages:

1. Relevance:
   Identify candidates that contain evidence genuinely relevant to
   the question.

2. Evidence quality:
   Determine whether each relevant candidate actually supports a
   claim, rather than merely mentioning that somebody has made the
   claim.

3. Conflict resolution:
   If relevant candidates disagree, determine which claims are best
   supported by the quality and nature of the evidence.

Important distinctions:

- A source reporting that a historical figure, politician, scientist,
  or other person once believed something does NOT establish that
  belief as fact.
- A historical theory may be important to mention while still being
  rejected, disputed, outdated, or unsupported by modern scholarship.
- Do not treat every explanation presented by a source as equally
  credible.
- Distinguish established findings from disputed theories and from
  speculative or weak claims.
- Prefer modern scholarly consensus when the question asks what is
  generally accepted today.
- Prefer primary or official sources where appropriate.
- Prefer authoritative specialist sources over general-interest
  websites.
- Prefer explicit dates over vague or undated claims.
- Pay attention to whether a source is describing historical
  scholarship rather than presenting that scholarship as current fact.
- Do not promote a claim merely because several low-quality sources
  repeat it.
- A source can be relevant without being reliable evidence for its
  particular claim.
- If the evidence genuinely cannot establish an answer, say so.
- Do not use your own general knowledge to fill gaps.
- Do not invent missing facts.

For every supporting candidate, it should be possible to explain why
that candidate provides reliable evidence for the answer, rather than
merely evidence that a claim exists.

Return JSON only:

{{
    "answer": "best-supported answer",
    "confidence": "high|medium|low",
    "supporting_candidates": [1, 2],
    "rejected_candidates": [3],
    "reason": "brief explanation of why the selected evidence is reliable and why rejected or weaker claims were not used"
}}
"""

    return generate_json(prompt)


def select_evidence(candidates, evaluation):
    """Return the evidence candidates selected by the research judge."""

    selected = []

    for index in evaluation["supporting_candidates"]:
        selected.append(candidates[index - 1])

    return selected
