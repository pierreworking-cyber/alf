"""
Question interpretation for ALF.

Provides a small boundary between ALF's original user questions and
language-model reformulation for research.
"""

from .llm import _generate


def interpret_question(question):
    """
    Reformulate a user's question for research when necessary.
    """

    prompt = f"""
You are preparing a user's question for a research search.

Your task is to determine whether the question is already clear and
suitable for research.

If the question is already clear and suitable for research, return it
unchanged.

If the question is ambiguous, awkward, or likely to produce poor search
results, reformulate it into a clearer question that is suitable for
research.

Do not answer the question.
Do not provide an explanation.
Do not add facts that are not implied by the question.
Do not change the subject of the question.
Preserve the meaning of the user's question.
Preserve useful and specific terminology already present in the question.
Do not replace terminology merely to make the wording sound more natural.

Return only the question.

User's question:
{question}
"""

    return _generate(prompt).strip()
