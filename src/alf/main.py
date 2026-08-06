#!/usr/bin/env python3

"""
ALF - Peter's local computing companion.

"""

from .commands import run
from .presentation import render_ready
from .status import get_status_information
from .time import get_greeting


def introduce():
    print()
    print()
    print(f"{get_greeting()}, Peter.")

    render_ready(get_status_information())


def main():
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]
        arguments = sys.argv[2:]
        if run(command, arguments):
            return

        print(f"Unknown command: {command}")
        print("Try: alf help")
        return

    introduce()


if __name__ == "__main__":
    main()
