"""
Local language model interface.

Provides a small boundary between ALF and the local Ollama service.
"""

import json
from urllib.request import Request, urlopen

from .personality import ALF_PERSONALITY

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "qwen3:8b"


def ask(question):
    """
    Send a question to the local language model and return its answer.
    """

    prompt = f"""
{ALF_PERSONALITY}

Peter's question:

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
