"""
ALF command dispatcher.
"""

from .system import get_system_report


def run(command: str):
    """
    Execute an ALF command.

    Returns True if the command was recognised.
    """

    if command == "status":
        print()
        print(get_system_report())
        print()
        return True

    return False
