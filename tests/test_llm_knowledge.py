import os
import re

import pytest

from alf import llm
from tests.knowledge_corpus import KNOWLEDGE_TESTS

KNOWLEDGE_MODEL = os.environ.get(
    "ALF_KNOWLEDGE_MODEL",
    llm.OLLAMA_MODEL,
)

llm.OLLAMA_MODEL = KNOWLEDGE_MODEL


def normalise(text):
    """Normalise an LLM response for deterministic comparison."""
    return re.sub(r"\s+", " ", text.strip().lower())


def answer_passes(test, answer):
    """Determine whether an LLM answer satisfies a corpus entry."""
    answer = normalise(answer)

    if test["type"] == "exact":
        return any(normalise(expected) == answer for expected in test["expected"])

    if test["type"] == "contains":
        return any(normalise(expected) in answer for expected in test["expected"])

    raise ValueError(f"Unknown knowledge test type: {test['type']}")


@pytest.mark.parametrize(
    "test",
    KNOWLEDGE_TESTS,
    ids=lambda test: test["question"],
)
def test_llm_knowledge(test):
    answer = llm._generate(
        f"""
Answer the following factual question.

Give a concise answer.
Do not explain your reasoning.

Question:
{test["question"]}
"""
    )

    assert answer_passes(test, answer), (
        f"\nQuestion: {test['question']}"
        f"\nExpected: {test['expected']}"
        f"\nActual: {answer!r}"
    )
