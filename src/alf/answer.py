from .llm import ask


def prepare_answer(question, evidence):
    """
    Prepare an answer request and send it to the language model.
    """

    answer_request = {
        "question": question,
        "evidence": evidence,
    }

    return ask(answer_request)
