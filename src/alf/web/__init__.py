"""
ALF's web interface.

This module provides the Flask application used by ``alf web``.
"""

from flask import Flask, render_template, request

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


def main() -> None:
    """Start ALF's web interface."""

    app.run()
