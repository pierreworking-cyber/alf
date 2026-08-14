"""
Deterministic resolution of ALF commands and contextual vocabulary.

This module deliberately performs only small, unambiguous vocabulary
resolution. It does not attempt to infer natural-language intent.
"""

from .command_catalogue import commands
from .memory import get_memory_categories


def get_command_matches(value):
    """
    Return commands matching an exact name or leading prefix.
    """

    value = value.strip().lower()

    if not value:
        return []

    if value in commands:
        return [value]

    return [
        command
        for command in commands
        if command.startswith(value)
    ]


def resolve_command(value):
    """
    Resolve an exact command or an unambiguous leading prefix.

    Returns the canonical command name, or None if the value is unknown
    or ambiguous.
    """

    matches = get_command_matches(value)

    if len(matches) == 1:
        return matches[0]

    return None


def resolve_category(value):
    """
    Resolve an exact memory category or an unambiguous leading prefix.

    Simple plural forms such as 'notes' are also accepted when they map
    directly to a canonical category.

    Returns the canonical category name, or None if unresolved.
    """

    value = value.strip().lower()

    categories = get_memory_categories()

    if value in categories:
        return value

    if value.endswith("s") and value[:-1] in categories:
        return value[:-1]

    matches = [
        category
        for category in categories
        if category.startswith(value)
    ]

    if len(matches) == 1:
        return matches[0]

    return None
