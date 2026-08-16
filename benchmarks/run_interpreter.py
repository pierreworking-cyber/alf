"""
Run the exploratory ALF interpreter qualification benchmark.

This benchmark talks directly to Ollama rather than through ALF's
production LLM interface so that the complete model response and
generation metadata remain available for analysis.
"""

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import Request, urlopen

from interpreter_corpus import INTERPRETER_TESTS

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = os.environ.get("ALF_BENCHMARK_MODEL", "qwen3:4b")
RESULTS_DIR = Path(__file__).parent

class Tee:
    """Write output to both the terminal and a result file."""

    def __init__(self, terminal, file):
        self.terminal = terminal
        self.file = file

    def write(self, text):
        """Write text to both output destinations."""
        self.terminal.write(text)
        self.file.write(text)

    def flush(self):
        """Flush both output destinations."""
        self.terminal.flush()
        self.file.flush()


def generate(prompt):
    """Send a prompt to Ollama and return the complete response."""
    payload = json.dumps(
        {
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "think": False,
        }
    ).encode("utf-8")
    request = Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request) as response:
        return json.load(response)


def build_prompt(test):
    """Build the interpretation prompt used for a corpus case."""
    return f"""
You are preparing a user's question for a research search.

Your task is to determine whether the question is already clear and
suitable for research.

    If the question is already clear and suitable for research, return it
    exactly unchanged.

    If the question is ambiguous, awkward, or likely to produce poor search
    results, reformulate it into a clearer question that is suitable for
    research.

    Do not answer the question.
    Do not provide an explanation.
    Do not add facts that are not implied by the question.
    Do not change the subject of the question.
    Preserve the meaning of the user's question.
    When preserving the question, preserve its exact wording, punctuation,
    quotation marks, technical identifiers, command-line options, and other
    literal syntax.
    Preserve useful and specific terminology already present in the question.
    Do not replace terminology merely to make the wording sound more natural.

Return only the question.

User's question:
{test["question"]}
""".strip()


def normalise(text):
    """Normalise whitespace for basic benchmark comparisons."""
    return " ".join(text.strip().split())


def evaluate(test, response):
    """Apply the initial exploratory checks to a model response."""
    answer = response.get("response", "").strip()
    normalised_answer = normalise(answer)
    failures = []

    if test["mode"] == "preserve":
        expected = normalise(test["question"])

        if normalised_answer != expected:
            failures.append("question was not preserved unchanged")

    for required in test["required"]:
        if required.lower() not in answer.lower():
            failures.append(f"required text missing: {required!r}")

    return {
        "passed": not failures,
        "failures": failures,
        "answer": answer,
    }


def format_duration(nanoseconds):
    """Convert Ollama nanoseconds to seconds for display."""
    if nanoseconds is None:
        return "n/a"

    return f"{nanoseconds / 1_000_000_000:.3f}s"


def run_case(test):
    """Run and evaluate one corpus case."""
    response = generate(build_prompt(test))
    evaluation = evaluate(test, response)

    return {
        "test": test,
        "response": response,
        "evaluation": evaluation,
    }


def print_case(result, number, total):
    """Print one benchmark case in a human-readable form."""
    test = result["test"]
    response = result["response"]
    evaluation = result["evaluation"]

    print()
    print("─" * 72)
    print(f"CASE {number:02d}/{total:02d} — {test['name'].upper()}")
    print("─" * 72)

    print()
    print("Input:")
    print(test["question"])

    if test["required"]:
        print()
        print("Required:")
        for item in test["required"]:
            print(f"  {item}")

    print()
    print("Model response:")
    print(evaluation["answer"])

    print()
    print(f"Result: {'PASS' if evaluation['passed'] else 'FAIL'}")

    if evaluation["failures"]:
        print()
        print("Failures:")
        for failure in evaluation["failures"]:
            print(f"  - {failure}")

    print()
    print(f"Output tokens:       {response.get('eval_count', 'n/a')}")
    print(
        "Total duration:      "
        f"{format_duration(response.get('total_duration'))}"
    )
    print(
        "Load duration:       "
        f"{format_duration(response.get('load_duration'))}"
    )
    print(
        "Prompt evaluation:   "
        f"{format_duration(response.get('prompt_eval_duration'))}"
    )
    print(
        "Generation duration: "
        f"{format_duration(response.get('eval_duration'))}"
    )

    thinking = response.get("thinking", "")

    print()
    print("Thinking:")
    print(thinking.strip() if thinking.strip() else "(none)")


def print_summary(results):
    """Print an exploratory summary without declaring qualification."""
    passed = sum(
        1
        for result in results
        if result["evaluation"]["passed"]
    )

    failed = len(results) - passed

    print()
    print()
    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print()
    print(f"Cases:                 {len(results)}")
    print(f"Passed:                {passed}")
    print(f"Failed:                {failed}")
    print()

    for mode in ("preserve", "reformulate"):
        mode_results = [
            result
            for result in results
            if result["test"]["mode"] == mode
        ]

        if mode_results:
            mode_passed = sum(
                1
                for result in mode_results
                if result["evaluation"]["passed"]
            )

            print(
                f"{mode.capitalize():<22}"
                f"{mode_passed}/{len(mode_results)}"
            )

    print()
    print("Cases requiring review:")

    reviewed = False

    for result in results:
        if not result["evaluation"]["passed"]:
            reviewed = True
            print(
                f"  {result['test']['id']} — "
                f"{result['test']['name']}"
            )

    if not reviewed:
        print("  None")


def warm_model():
    """Warm the selected model before benchmark measurements begin."""
    generate("Reply with exactly: test")


def main():
    """Run the complete exploratory benchmark."""
    started = datetime.now(UTC)
    timestamp = started.strftime("%Y-%m-%d_%H%M%S")
    result_file = (
        RESULTS_DIR
        / f"interpreter_results_{MODEL.replace(':', '-')}_{timestamp}.txt"
    )

    with result_file.open("w", encoding="utf-8") as file:
        original_stdout = sys.stdout
        sys.stdout = Tee(original_stdout, file)

        try:
            print("=" * 72)
            print("ALF INTERPRETER QUALIFICATION — EXPLORATORY RUN")
            print("=" * 72)
            print()
            print(f"Model:  {MODEL}")
            print(f"Cases:  {len(INTERPRETER_TESTS)}")
            print(f"Started: {started.isoformat()}")
            print()
            print("Warming model...")
            warm_model()
            print("Model ready.")

            results = []

            for number, test in enumerate(INTERPRETER_TESTS, start=1):
                result = run_case(test)
                results.append(result)
                print_case(result, number, len(INTERPRETER_TESTS))

            print_summary(results)
        finally:
            sys.stdout = original_stdout


if __name__ == "__main__":
    main()
