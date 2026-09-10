"""
Routing questions that may require external evidence.
"""

from .llm import generate_json


def needs_research(question):
    """Return True when a question should be answered using external evidence."""

    prompt = f"""
You are ALF's research router.

Your ONLY job is to decide whether answering the user's question
properly requires external evidence.

Return exactly one JSON object:

{{
  "route": "LLM" or "RESEARCH",
  "reason": "short explanation"
}}

Use these rules:

LLM:
The question can be answered reliably from stable general knowledge
or ordinary explanation. It does not require current, changing,
statistical, disputed, or externally verified information.

RESEARCH:
A reliable answer requires external evidence. This includes current
or changing facts, historical figures or events where accuracy matters,
statistics, prices, laws, political information, recent developments,
comparisons that depend on current evidence, disputed claims, or
questions where evidence from several sources would improve the answer.

Do not answer the question.
Return valid JSON only.

User question:
{question}
"""

    decision = generate_json(prompt)

    return decision["route"] == "RESEARCH"
