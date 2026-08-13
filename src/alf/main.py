#!/usr/bin/env python3

"""
ALF - Peter's local computing companion.

"""

from .commands import help_command, run, show_status
from .presentation import (
    error,
    info,
    render_greeting,
)
from .time import get_greeting


def introduce():
    render_greeting(f"{get_greeting()}, Peter.")
    (show_status,)


def main():
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] in ("--help", "-h"):
            help_command()
            return

        command = sys.argv[1]
        arguments = sys.argv[2:]
        if run(command, arguments):
            return

        error(f"Unknown command: {command}")
        info("Try: alf help")
        return

    introduce()


if __name__ == "__main__":
    main()
