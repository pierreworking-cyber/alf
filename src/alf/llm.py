"""
Local language model interface.

Provides a small boundary between ALF and the local Ollama service.
"""

import json
from urllib.request import Request, urlopen

from .personality import ALF_PERSONALITY

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_TAGS_URL = "http://127.0.0.1:11434/api/tags"
OLLAMA_MODEL = "qwen3:8b"


def ask(question, research):
    """
    Send a question and optional Wikipedia research to the local language model.
    """

    if research is None:
        research_text = "No Wikipedia research was available."
    else:
        research_text = research["text"]

    prompt = f"""
{ALF_PERSONALITY}

You are answering the user's question as the voice of ALF.

Wikipedia research supplied by ALF:

{research_text}

User's question:

{question}
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

    with urlopen(request) as response:
        result = json.load(response)

    return result["response"]


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
