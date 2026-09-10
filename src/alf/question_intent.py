"""
Simple intent checks for ALF questions.

This module distinguishes requests for ALF to perform an action from
questions asking for information or instructions.
"""


def is_action_request(question):
    """Return True when the question directly asks ALF to perform an action."""

    text = question.strip().lower()

    if not text:
        return False

    explanatory_starts = (
        "how do i ",
        "how can i ",
        "what do i ",
        "what is ",
        "what does ",
        "why ",
        "when ",
        "where ",
        "who ",
        "which ",
        "can you explain ",
        "tell me about ",
    )

    if text.startswith(explanatory_starts):
        return False

    action_starts = (
        "make ",
        "create ",
        "delete ",
        "remove ",
        "rename ",
        "move ",
        "copy ",
        "open ",
        "close ",
        "start ",
        "stop ",
        "run ",
        "install ",
        "uninstall ",
        "send ",
        "write ",
        "change ",
        "turn ",
        "restart ",
        "shut down ",
    )

    return text.startswith(action_starts)
