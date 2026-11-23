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
    router_failed = False

    try:
        research_required = needs_research(original_question)
    except Exception:
        research_required = True
        router_failed = True

    router_time = time.perf_counter() - router_start
    timings: dict[str, float] = {"router": router_time}

    if research_required:
        report("Researching…")

        if router_failed:
            report("Research routing failed; continuing cautiously…")

        research_timings: dict[str, float] = {}
        research_start = time.perf_counter()
        try:
            candidates = research(
                original_question,
                timings=research_timings,
            )
        except Exception:
            candidates = []
        timings["research"] = time.perf_counter() - research_start
        timings.update(research_timings)

        evidence = []
        judgement = None

        if candidates:
            judge_start = time.perf_counter()
            try:
                evaluation = evaluate_evidence(
                    original_question,
                    candidates,
                )
            except Exception:
                evaluation = None
            timings["evidence_judge"] = time.perf_counter() - judge_start

            if isinstance(evaluation, dict):
                answer_text = evaluation.get("answer")
                confidence = evaluation.get("confidence")
                supporting = evaluation.get("supporting_candidates")
                rejected = evaluation.get("rejected_candidates")
                reason = evaluation.get("reason")

                valid_evaluation = (
                    isinstance(answer_text, str)
                    and bool(answer_text.strip())
                    and confidence in ("high", "medium")
                    and isinstance(supporting, list)
                    and isinstance(rejected, list)
                    and isinstance(reason, str)
                    and all(
                        type(index) is int
                        and 1 <= index <= len(candidates)
                        for index in supporting
                    )
                    and all(
                        type(index) is int
                        and 1 <= index <= len(candidates)
                        for index in rejected
                    )
                )

                if valid_evaluation and supporting:
                    try:
                        selected = select_evidence(
                            candidates,
                            evaluation,
                        )
                    except Exception:
                        selected = []

                    if selected:
                        evidence = selected
                        judgement = answer_text

        if evidence:
            report("Asking language model…")

            answer_start = time.perf_counter()
            try:
                answer = prepare_answer(
                    original_question,
                    evidence=evidence,
                    research_judgement=judgement,
                    verbose=verbose,
                )
            except Exception:
                return QuestionResult(
                    answer=(
                        "I couldn't reach the language model. Check that "
                        "the configured Ollama service is running and try "
                        "again."
                    ),
                    source=None,
                    timings=timings,
                )
            timings["answer"] = time.perf_counter() - answer_start

            return QuestionResult(
                answer=answer,
                source="research",
                timings=timings,
            )

        report("Research unavailable; answering from model knowledge…")

    else:
        report("Asking language model…")

    answer_start = time.perf_counter()
    try:
        if research_required:
            answer = prepare_answer(
                original_question,
                verbose=verbose,
                research_unavailable=True,
            )
        else:
            answer = prepare_answer(
                original_question,
                verbose=verbose,
            )
    except Exception:
        return QuestionResult(
            answer=(
                "I couldn't reach the language model. Check that the "
                "configured Ollama service is running and try again."
            ),
            source=None,
            timings=timings,
        )
    timings["answer"] = time.perf_counter() - answer_start

    return QuestionResult(
        answer=answer,
        source="llm",
        timings=timings,
    )
