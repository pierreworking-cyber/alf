"""ALF's answer-routing boundary."""

from .classifier import classify
from .news_intent import interpret_news_question
from .routes import Route


def route(question):
    """
    Decide which ALF capability should handle a question.

    News questions are recognised deterministically first, before the
    language model is consulted, so clear current-events questions are
    routed without waiting on or trusting the model. Anything else falls
    through to the model-based classifier.
    """
    if interpret_news_question(question) is not None:
        return Route.NEWS

    return classify(question)
