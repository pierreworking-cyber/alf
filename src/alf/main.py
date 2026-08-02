#!/usr/bin/env python3

"""
ALF - Peter's local computing companion.

"""

from .identity import describe_identity
from .commands import run
from .time import get_greeting


def introduce():
    print()
    print()
    print(f"{get_greeting()}, Peter.")

    describe_identity()


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
