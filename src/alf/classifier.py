"""
Question classification for ALF's answer router.
"""

from . import llm
from .routes import Route

EXAMPLES = [
    ("What operating system am I running?", Route.SYSTEM),
    ("What OS is this machine running?", Route.SYSTEM),
    ("What GPU is in this computer?", Route.SYSTEM),
    ("What did we decide about SearXNG?", Route.MEMORY),
    ("What did I ask you to remember about ALF?", Route.MEMORY),
    ("What have we previously decided about the project?", Route.MEMORY),
    ("What is the latest version of Python?", Route.RESEARCH),
    ("Who is the current Prime Minister of the UK?", Route.RESEARCH),
    ("What is the weather forecast for tomorrow?", Route.RESEARCH),
    ("What does pytest -q mean?", Route.LLM),
    ("What is the difference between a list and a tuple in Python?", Route.LLM),
    ("What does a Python virtual environment do?", Route.LLM),
    ("Can ALF physically repair my computer?", Route.DECLINE),
    ("Can you make me a cup of tea?", Route.DECLINE),
]


def classify(question):
    """Classify a question into one of ALF's routing categories."""

    examples = "\n".join(
        f"{example_question} -> {route.value}"
        for example_question, route in EXAMPLES
    )

    prompt = f"""
Classify the user's question into exactly one of these categories:

system
memory
research
llm
decline

SYSTEM means the question requires information about this computer.

MEMORY means the question asks about something Peter and ALF previously
remembered, discussed, or decided.

RESEARCH means the question requires current or external information.

LLM means the question can be answered from general knowledge.

DECLINE means ALF has no suitable capability or reliable source.

Use the examples below as guidance.

Examples:
{examples}

Return exactly one category name and nothing else.

User's question:
{question}
"""

    result = llm._generate(prompt).strip().lower()

    try:
        return Route(result)
    except ValueError as error:
        raise ValueError(f"Invalid routing classification: {result}") from error
