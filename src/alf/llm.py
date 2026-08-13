"""
Local language model interface.

Provides a small boundary between ALF and the local Ollama service.
"""

import json
from urllib.request import Request, urlopen

from .personality import ALF_PERSONALITY

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_TAGS_URL = "http://127.0.0.1:11434/api/tags"
OLLAMA_MODEL = "qwen3:4b"


def _generate(prompt):
    """Send a prompt to the configured local language model."""
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

    with urlopen(request) as response:
        result = json.load(response)

    return result["response"]


def ask(answer_request):
    """
    Send an answer request to the local language model.
    """

    question = answer_request["question"]
    evidence = answer_request["evidence"]

    if evidence:
        evidence_text = str(evidence)
    else:
        evidence_text = "No evidence was available."

    prompt = f"""
{ALF_PERSONALITY}

You are answering the user's question as the voice of ALF.

Evidence supplied by ALF:

{evidence_text}

User's question:

{question}
"""

    return _generate(prompt)


def evaluate_research(question, candidates):
    """
    Ask the local language model whether the supplied research is relevant.
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

    response = _generate(prompt)

    try:
        evaluation = json.loads(response)
    except (json.JSONDecodeError, TypeError, KeyError) as error:
        raise ValueError("Invalid research evaluation response") from error

    return {
        "relevant": evaluation.get("relevant", False),
        "candidates": evaluation.get("candidates", []),
        "reason": evaluation.get("reason", ""),
    }


def check_ollama():
    """
    Check whether Ollama is available and ALF's configured model is installed.
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
