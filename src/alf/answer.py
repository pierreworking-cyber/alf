"""
ALF answer preparation.

Combines a question with capability evidence.
"""


def prepare_answer(question, evidence):
    """
    Prepare an answer request from a question and supplied evidence.
    """

    return {
        "question": question,
        "evidence": evidence,
    }
