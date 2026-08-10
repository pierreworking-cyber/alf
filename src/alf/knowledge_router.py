"""
Deterministic knowledge routing for ALF.

Decides which ALF knowledge sources should be considered for a question.
"""

import re

from .memory import search_memories

STOP_WORDS = {
    "a",
    "about",
    "after",
    "all",
    "an",
    "and",
    "are",
    "at",
    "be",
    "been",
    "between",
    "by",
    "did",
    "do",
    "during",
    "for",
    "from",
    "happened",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "of",
    "on",
    "or",
    "tell",
    "the",
    "think",
    "to",
    "was",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
}


def extract_terms(question):
    """
    Extract useful terms from a natural-language question.

    Common grammatical and conversational words are ignored so that
    memory searches concentrate on potentially meaningful terms.
    """
    words = re.findall(r"[A-Za-z0-9]+", question.lower())

    return [
        word
        for word in words
        if word not in STOP_WORDS and len(word) > 2
    ]


def find_memory_matches(terms):
    """
    Find memories containing one or more question terms.
    """
    matches = {}

    for term in terms:
        for memory in search_memories(term):
            matches.setdefault(memory["id"], memory)

    return list(matches.values())


def get_matched_terms(terms, memories):
    """
    Identify question terms represented in the candidate memories.
    """
    matched_terms = []

    for term in terms:
        if any(term in memory["content"].lower() for memory in memories):
            matched_terms.append(term)

    return matched_terms


def get_coverage(terms, matched_terms):
    """
    Calculate the proportion of question terms found in memory.
    """
    if not terms:
        return 0.0

    return len(matched_terms) / len(terms)


def route_question(question):
    """
    Decide whether ALF should use memory or external research.

    An explicit --research suffix overrides normal routing.
    """
    force_research = question.rstrip().endswith("--research")

    if force_research:
        question = question.rstrip()[:-len("--research")].rstrip()

    terms = extract_terms(question)
    matches = find_memory_matches(terms)
    matched_terms = get_matched_terms(terms, matches)
    coverage = get_coverage(terms, matched_terms)

    if force_research:
        decision = "research"
        reason = "User explicitly requested external research."

    elif matched_terms:
        decision = "memory"
        reason = "Memory contains potentially relevant terms."

    else:
        decision = "research"
        reason = "No memory matched the question terms."

    return {
        "decision": decision,
        "reason": reason,
        "terms": terms,
        "matched_terms": matched_terms,
        "coverage": coverage,
        "matches": matches,
    }
