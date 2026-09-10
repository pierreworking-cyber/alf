"""
Answer preparation for ALF.

This module prepares the structured request passed to the language-model
layer.
"""

from .llm import ask


def prepare_answer(
    question: str,
    evidence=None,
    verbose: bool = False,
):
    """Prepare a question request and send it to the language-model layer.

    Args:
        question: The question as entered by the user.
        verbose: Whether to request a more detailed response.

    Returns:
        The answer produced by the language-model layer.
    """

    answer_request = {
        "question": question,
        "evidence": evidence,
        "verbose": verbose,
    }

    return ask(answer_request)
