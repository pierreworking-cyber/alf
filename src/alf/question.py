"""
ALF question-processing engine.
"""

from collections.abc import Callable
from dataclasses import dataclass

from .answer import prepare_answer
from .interpretation import interpret_question
from .llm import evaluate_research
from .research import research_web, research_wikipedia_candidates
from .router import route
from .routes import Route


@dataclass
class QuestionResult:
    """Result returned by the question-processing engine."""

    answer: str
    source: str | None
    research_question: str


def answer_question(
    original_question: str,
    verbose: bool = False,
    progress: Callable[[str], None] | None = None,
) -> QuestionResult:
    """
    Process a question and return the resulting answer.

    The optional progress callback receives descriptions of the
    significant stages of question processing.
    """

    def report(message: str) -> None:
        if progress is not None:
            progress(message)

    report("Routing question…")
    selected_route = route(original_question)

    if selected_route == Route.LLM:
        report("Asking local language model…")

        answer = prepare_answer(
            original_question,
            original_question,
            [],
            verbose=verbose,
        )

        return QuestionResult(
            answer=answer,
            source="llm",
            research_question=original_question,
        )

    report("Interpreting question…")
    research_question = interpret_question(original_question)

    report("Researching Wikipedia…")
    candidates = research_wikipedia_candidates(research_question)

    report("Evaluating Wikipedia evidence…")
    evaluation = evaluate_research(research_question, candidates)

    if evaluation["relevant"]:
        relevant_candidates = [
            candidates[index - 1]
            for index in evaluation["candidates"]
            if 1 <= index <= len(candidates)
        ]

        if relevant_candidates:
            report("Asking local language model…")

            answer = prepare_answer(
                original_question,
                research_question,
                [relevant_candidates[0]],
                verbose=verbose,
            )

            return QuestionResult(
                answer=answer,
                source="wikipedia",
                research_question=research_question,
            )

    report("Researching the web…")
    web_candidates = research_web(research_question)

    report("Evaluating web evidence…")
    web_evaluation = evaluate_research(
        research_question,
        web_candidates,
    )

    if web_evaluation["relevant"]:
        relevant_candidates = [
            web_candidates[index - 1]
            for index in web_evaluation["candidates"]
            if 1 <= index <= len(web_candidates)
        ]

        if relevant_candidates:
            report("Asking local language model…")

            answer = prepare_answer(
                original_question,
                research_question,
                [relevant_candidates[0]],
                verbose=verbose,
            )

            return QuestionResult(
                answer=answer,
                source="web",
                research_question=research_question,
            )

    return QuestionResult(
        answer=(
            "I couldn't find reliable research that answers your question. "
            "I don't want to guess."
        ),
        source=None,
        research_question=research_question,
    )
