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
from urllib.request import Request, urlopen

from .personality import ALF_PERSONALITY

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_TAGS_URL = "http://127.0.0.1:11434/api/tags"
OLLAMA_MODEL = "qwen3:8b"


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
