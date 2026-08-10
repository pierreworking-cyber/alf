"""
Local language model interface.

Provides a small boundary between ALF and the local Ollama service.
"""

import json
from urllib.request import Request, urlopen

from .personality import ALF_PERSONALITY

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "qwen3:8b"


def ask(question, research):
    """
    Send a question and Wikipedia research to the local language model.
    """

    prompt = f"""
{ALF_PERSONALITY}

You are answering the user's question using Wikipedia research supplied by ALF.

Answer the user's actual question directly.
Use the supplied research as evidence and context.
Do not introduce unrelated information.
Do not invent facts that are not supported by the supplied research.
If the research does not contain enough information to answer confidently,
say so.

User's question:

{question}

Wikipedia research supplied by ALF:

{research["text"]}
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
