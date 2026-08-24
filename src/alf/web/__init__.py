"""
ALF's web interface.

This module provides the Flask application used by ``alf web``.
"""
import shlex

from flask import Flask, jsonify, render_template, request

from ..calc import CalculationError, calculate
from ..command_catalogue import commands
from ..memory import (
    find_related_memory_candidates,
    remember,
)
from ..question import answer_question

app = Flask(__name__)


@app.get("/")
def home():
    """Display the ALF web interface landing page."""
    return render_template("home.html")


@app.route("/question", methods=["GET", "POST"])
def question():
    """Display the ALF Question workspace and process questions."""

    question = ""
    verbose = False
    status = "Ready"
    answer = "Your answer will appear here."
    source = "—"

    if request.method == "POST":
        question = request.form.get("question", "").strip()
        verbose = request.form.get("verbose") == "on"

        if question:
            status = "Asking…"

            try:
                result = answer_question(
                    question,
                    verbose=verbose,
                )

                status = "Complete"
                answer = result.answer
                source = result.source or "No reliable source"

            except Exception as error:
                status = "Failed"
                answer = "I couldn't get an answer to the question."
                source = f"Error: {error}"

    return render_template(
        "question.html",
        question=question,
        verbose=verbose,
        status=status,
        answer=answer,
        source=source,
    )

@app.route("/remember", methods=["GET", "POST"])
def remember_memory():
    """Display the ALF Remember workspace and store memories."""

    category = "note"
    content = ""
    status = "Ready"

    if request.method == "POST":
        category = request.form.get("category", "note")
        content = request.form.get("content", "").strip()

        related_memory_ids = request.form.getlist("related_memory_ids")

        if not content:
            status = "Please enter something to remember."
        else:
            result = remember(
                category,
                content,
                related_memory_ids=",".join(related_memory_ids) or None,
            )

            if result:
                status = "Memory saved."
                content = ""
            else:
                status = "I couldn't save that memory."

    return render_template(
        "remember.html",
        category=category,
        content=content,
        status=status,
    )


@app.get("/remember/related")
def remember_related():
    """Return memories related to text being composed."""

    content = request.args.get("content", "").strip()

    if not content:
        return jsonify([])

    return jsonify(find_related_memory_candidates(content))



@app.route("/calc", methods=["GET", "POST"])
def calc():
    """Display the ALF Calculator workspace and process calculations."""

    expression = ""
    symbolic = False
    places = 3
    angle_mode = "radians"
    status = "Ready"
    result = "Your result will appear here."

    if request.method == "POST":
        expression = request.form.get("expression", "").strip()
        symbolic = request.form.get("symbolic") == "on"
        angle_mode = request.form.get("angle_mode", "radians")

        try:
            places = int(request.form.get("places", "3"))
        except ValueError:
            places = 3

        if expression:
            status = "Calculating…"

            try:
                calculation = calculate(
                    expression,
                    symbolic=symbolic,
                    places=places,
                    angle_mode=angle_mode,
                )

                status = "Complete"
                result = str(calculation)

            except CalculationError as error:
                status = "Could not calculate"
                result = str(error)

    symbolic_examples = commands["calc"]["examples"]["Symbolic mathematics"]

    examples = []

    for group_examples in commands["calc"]["examples"].values():
        for example in group_examples:
            parts = shlex.split(example)

            expression_parts = []
            example_angle_mode = "radians"

            for part in parts[2:]:
                if part == "--degrees":
                    example_angle_mode = "degrees"
                elif part == "--radians":
                    example_angle_mode = "radians"
                else:
                    expression_parts.append(part)

            expression = " ".join(expression_parts)

            examples.append(
                {
                    "expression": expression,
                    "symbolic": example in symbolic_examples,
                    "angle_mode": example_angle_mode,
                }
            )

    return render_template(
        "calc.html",
        expression=expression,
        symbolic=symbolic,
        places=places,
        angle_mode=angle_mode,
        status=status,
        result=result,
        examples=examples,
    )


def main() -> None:
    """Start ALF's web interface."""

    app.run()
