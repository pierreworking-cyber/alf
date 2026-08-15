from .llm import ask


def prepare_answer(
    original_question,
    research_question,
    evidence,
    verbose=False,
):
    """
    Prepare an answer request and send it to the language model.
    """

    answer_request = {
        "question": original_question,
        "research_question": research_question,
        "evidence": evidence,
        "verbose": verbose,
    }

    return ask(answer_request)
