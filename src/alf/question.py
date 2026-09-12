import time
from collections.abc import Callable
from dataclasses import dataclass, field

from .answer import prepare_answer
from .question_intent import is_action_request
from .research import evaluate_evidence, research, select_evidence
from .research_router import needs_research


@dataclass
class QuestionResult:
    answer: str
    source: str | None
    timings: dict[str, float] = field(default_factory=dict)


def answer_question(
    original_question: str,
    verbose: bool = False,
    progress: Callable[[str], None] | None = None,
) -> QuestionResult:
    def report(message: str) -> None:
        if progress is not None:
            progress(message)

    if is_action_request(original_question):
        return QuestionResult(
            answer="I can't perform actions like that.",
            source=None,
        )

    router_start = time.perf_counter()
    research_required = needs_research(original_question)
    router_time = time.perf_counter() - router_start

    if research_required:
        report("Researching…")

        try:
            research_timings = {}

            research_start = time.perf_counter()
            candidates = research(
                original_question,
                timings=research_timings,
            )
            research_time = time.perf_counter() - research_start

            judge_start = time.perf_counter()
            evaluation = evaluate_evidence(
                original_question,
                candidates,
            )
            judge_time = time.perf_counter() - judge_start

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

        answer_start = time.perf_counter()
        answer = prepare_answer(
            original_question,
            evidence=evidence,
            research_judgement=evaluation["answer"],
            verbose=verbose,
        )
        answer_time = time.perf_counter() - answer_start

        return QuestionResult(
            answer=answer,
            source="research",
            timings={
                "router": router_time,
                "research": research_time,
                **research_timings,
                "evidence_judge": judge_time,
                "answer": answer_time,
            },
        )

    report("Asking language model…")

    answer_start = time.perf_counter()
    answer = prepare_answer(
        original_question,
        verbose=verbose,
    )
    answer_time = time.perf_counter() - answer_start

    return QuestionResult(
        answer=answer,
        source="llm",
        timings={
            "router": router_time,
            "answer": answer_time,
        },
    )
