from enum import Enum


class Route(Enum):
    SYSTEM = "system"
    MEMORY = "memory"
    RESEARCH = "research"
    LLM = "llm"
    DECLINE = "decline"


def route(question):
    """
    Decide which ALF capability should handle a question.
    """
    question = question.lower()

    if "operating system" in question or "os am i" in question:
        return Route.SYSTEM

    return Route.LLM
