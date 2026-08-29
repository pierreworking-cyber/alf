"""
Local language-model interface for ALF.

This module provides the boundary between ALF and the local Ollama
service. It sends prompts to the configured model, builds answer
requests using ALF's personality and supplied evidence, evaluates
research candidates, and checks model availability.

The language model is treated as an interpreter of prompts and evidence;
it is not treated as an independent source of trusted knowledge.
"""

import json
from datetime import datetime
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .personality import ALF_PERSONALITY

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_TAGS_URL = "http://127.0.0.1:11434/api/tags"
OLLAMA_MODEL = "qwen3:8b"

NEWS_SYNTHESIS_LIMIT = 15


def generate(prompt):
    """
    Send a prompt to ALF's configured local language model.

    This is the low-level Ollama interface used by the higher-level
    functions in this module.

    Args:
        prompt: The complete prompt to send to the model.

    Returns:
        The text response returned by the language model.
    """
    payload = json.dumps(
        {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
        }
    ).encode("utf-8")

    request = Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=60) as response:
        result = json.load(response)

    return result["response"]


def ask(answer_request):
    """
    Ask the local language model to produce an answer for ALF.

    The request combines the user's original question with any evidence
    supplied by ALF and selects either a concise or detailed answer style.

    Args:
        answer_request: A dictionary containing the question, evidence,
            and optional ``verbose`` flag.

    Returns:
        The language model's generated answer.
    """

    question = answer_request["question"]
    evidence = answer_request["evidence"]
    verbose = answer_request.get("verbose", False)

    if evidence:
        evidence_text = str(evidence)
    else:
        evidence_text = "No evidence was available."

    if evidence:
        evidence_instruction = (
            "Answer using only the supplied evidence. "
            "Do not use your own general knowledge to fill gaps. "
            "If the evidence does not contain enough information to answer "
            "the question, say so clearly rather than guessing."
        )
    else:
        evidence_instruction = (
            "No evidence was supplied. You may answer from your general "
            "knowledge."
        )

    if verbose:
        answer_style = (
            "Give a detailed, well-developed answer. "
            "Provide useful context and explanation rather than "
            "a brief response."
        )
    else:
        answer_style = (
            "Give a concise but useful answer. "
            "Do not add unnecessary detail."
        )

    prompt = f"""
{ALF_PERSONALITY}

You are answering the user's question as the voice of ALF.

Evidence supplied by ALF:

{evidence_text}

Evidence handling:

{evidence_instruction}

User's question:

{question}

Answer style:

{answer_style}
"""

    return generate(prompt)


def evaluate_research(question, candidates):
    """
    Evaluate whether supplied research is relevant to a question.

    The local language model examines the supplied research candidates
    and identifies which candidates genuinely support answering the
    question. The model is instructed not to treat superficial word
    overlap as evidence of relevance.

    Args:
        question: The question the research should answer.
        candidates: Research candidates containing ``title`` and ``text``.

    Returns:
        A dictionary containing the relevance decision, relevant
        candidate numbers, and a brief explanation.

    Raises:
        ValueError: If the language model does not return valid JSON.
    """

    research_text = "\n\n".join(
        f"Candidate {index + 1}: {candidate['title']}\n{candidate['text']}"
        for index, candidate in enumerate(candidates)
    )

    prompt = f"""
You are evaluating research supplied to ALF.

Determine whether any of the supplied research is genuinely relevant
to answering the user's question.

Do not guess.
Do not infer relevance merely because words happen to overlap.
If the research does not support the question, mark it as not relevant.

Return JSON only in this form:

{{
    "relevant": true or false,
    "candidates": [numbers of relevant candidates],
    "reason": "brief explanation"
}}

User's question:
{question}

Research:
{research_text}
"""

    response = generate(prompt)

    try:
        evaluation = json.loads(response)
    except (json.JSONDecodeError, TypeError, KeyError) as error:
        raise ValueError("Invalid research evaluation response") from error

    return {
        "relevant": evaluation.get("relevant", False),
        "candidates": evaluation.get("candidates", []),
        "reason": evaluation.get("reason", ""),
    }


def synthesize_news(question, items, verbose=False):
    """
    Ask the local language model to synthesize a news answer.

    The supplied news items are the only evidence available to the model.
    ALF has already selected the items through news retrieval; the model
    interprets them for the user's question without selecting, ranking,
    or clustering them.

    Args:
        question: The user's original news question.
        items: The news item dictionaries selected by ALF's news retrieval.
        verbose: Whether to request a slightly fuller news update.

    Returns:
        The language model's synthesized news answer.
    """

    if verbose:
        answer_style = (
            "Give a slightly fuller update than usual, while remaining "
            "concise."
        )
    else:
        answer_style = "Keep the update concise."

    prompt = f"""
You are ALF, preparing a news update from ALF's stored news items.

The numbered articles below are the ONLY evidence you may use.

When answering the user's question, follow these rules:

- Do not invent facts or sources: add nothing beyond the supplied articles.
- If an article has no summary, rely only on its title.
- Answer as a news update of what the supplied articles say,
  not as general or encyclopedic knowledge.
- If the supplied articles conflict or report differently, say so,
  rather than silently choosing one side.
- Distinguish reported claims from established facts where appropriate.
- Cite supporting articles only as [1], [2], and so on, and
  only where those articles support the claim.
- If the supplied articles do not cover the user's question, say so
  plainly rather than guessing.

{answer_style}

Articles:

{_format_news_evidence(items[:NEWS_SYNTHESIS_LIMIT])}

User's question:

{question}
"""

    return generate(prompt)


def _format_news_evidence(items):
    """
    Format news items as numbered evidence for the language model.

    Each item is numbered, labelled with its subject, publication time,
    and a readable outlet label, and paired with its title and URL. The
    Summary line is included only when a summary is present.

    Args:
        items: The news item dictionaries to format.

    Returns:
        A numbered evidence text block.
    """

    lines = []

    for index, item in enumerate(items, start=1):
        title = item.get("title", "")
        url = item.get("url", "")
        published = _format_item_date(item.get("published_at"))
        label = _outlet_label(item.get("feed_title"))
        subject = item.get("subject", "News")

        detail = ", ".join(
            part for part in (subject, published, label) if part
        )

        lines.append(f"[{index}] {title} — {detail} — {url}")

        summary = item.get("summary")

        if summary:
            lines.append(f"    Summary: {summary}")

    return "\n".join(lines)


def _outlet_label(feed_title):
    """
    Derive a readable outlet label from a feed URL.

    The URL remains the authoritative source identifier; the label is a
    presentation convenience and never invents a publisher identity.
    """

    if not feed_title:
        return None

    try:
        host = urlparse(feed_title).hostname or ""
    except ValueError:
        return None

    host = host.removeprefix("www.").removeprefix("feeds.")
    label = host.split(".", 1)[0]

    return label.capitalize() or None


def _format_item_date(published_at):
    """
    Format an item's publication timestamp for display in evidence.
    """

    if not published_at:
        return ""

    try:
        return datetime.fromisoformat(
            published_at.replace("Z", "+00:00")
        ).strftime("%d-%b-%Y %H:%M")
    except ValueError:
        return ""


def check_ollama():
    """
    Check availability of the Ollama service and configured model.

    The service is queried for its installed models. A successful
    connection does not by itself mean ALF can use the configured model;
    both service availability and model availability are reported.

    Returns:
        A dictionary containing service availability, model availability,
        the configured model name, and any connection error.
    """

    request = Request(OLLAMA_TAGS_URL)

    try:
        with urlopen(request, timeout=2) as response:
            data = json.load(response)

    except Exception as error:
        return {
            "available": False,
            "model_available": False,
            "model": OLLAMA_MODEL,
            "error": str(error),
        }

    models = [
        model.get("name")
        for model in data.get("models", [])
    ]

    return {
        "available": True,
        "model_available": OLLAMA_MODEL in models,
        "model": OLLAMA_MODEL,
        "error": None,
    }
