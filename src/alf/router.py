"""ALF's answer-routing boundary."""

from .classifier import classify
from .routes import Route


def route(question):
    """
    Decide which ALF capability should handle a question.
    """
    return classify(question)
