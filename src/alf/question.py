"""
Question processing for ALF.

This module sends user questions to the answer-generation layer and returns
the resulting answer.
"""

from collections.abc import Callable
from dataclasses import dataclass

from .answer import prepare_answer


@dataclass
class QuestionResult:
    """Result produced by the question-processing engine.

    Attributes:
        answer: The final answer presented to the user.
        source: The source used to produce the answer.
    """

    answer: str
    source: str | None


def answer_question(
    original_question: str,
    verbose: bool = False,
    progress: Callable[[str], None] | None = None,
) -> QuestionResult:
    """Send a user question to the language model and return the answer.

    Args:
        original_question: The question as entered by the user.
        verbose: Whether to request a more detailed answer.
        progress: Optional callback used to report question processing stages.

    Returns:
        A ``QuestionResult`` containing the answer and its source.
    """

    def report(message: str) -> None:
        if progress is not None:
            progress(message)

    report("Asking language model…")

    answer = prepare_answer(
        original_question,
        verbose=verbose,
    )

    return QuestionResult(
        answer=answer,
        source="llm",
    )
