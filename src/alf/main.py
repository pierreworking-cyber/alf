#!/usr/bin/env python3

"""
ALF - Peter's local computing companion.

"""

from .commands import run
from .identity import get_about_information
from .presentation import (
    error,
    info,
    render_about,
    render_greeting,
)
from .time import get_greeting


def introduce():
    render_greeting(f"{get_greeting()}, Peter.")

    render_about(get_about_information())


def main():
    import sys

    if len(sys.argv) > 1:
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
