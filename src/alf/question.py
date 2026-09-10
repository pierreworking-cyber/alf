"""
Question processing for ALF.

This module sends user questions to the answer-generation layer and returns
the resulting answer.
"""

from collections.abc import Callable
from dataclasses import dataclass

from .answer import prepare_answer
from .question_intent import is_action_request
from .research import evaluate_evidence, research, select_evidence
from .research_router import needs_research


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
    """Send a user question to the appropriate answer path.

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

    if is_action_request(original_question):
        return QuestionResult(
            answer="I can't perform actions like that.",
            source=None,
        )

    if needs_research(original_question):
        report("Researching…")

        try:
            candidates = research(original_question)
            evaluation = evaluate_evidence(
                original_question,
                candidates,
            )
            evidence = select_evidence(
                candidates,
                evaluation,
            )
        except Exception:
            return QuestionResult(
                answer=(
                    "I couldn't retrieve reliable research for that "
                    "question, so I don't want to guess."
                ),
                source=None,
            )

        if not evidence:
            return QuestionResult(
                answer=(
                    "I couldn't find enough reliable evidence to answer "
                    "that confidently."
                ),
                source=None,
            )

        report("Asking language model…")

        answer = prepare_answer(
            original_question,
            evidence=evidence,
            verbose=verbose,
        )

        return QuestionResult(
            answer=answer,
            source="research",
        )

    report("Asking language model…")

    answer = prepare_answer(
        original_question,
        verbose=verbose,
    )

    return QuestionResult(
        answer=answer,
        source="llm",
    )
