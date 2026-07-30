#!/usr/bin/env python3

"""
ALF - Peter's local computing companion.

"""

from .identity import get_identity
from .commands import run
from .time import get_greeting

def introduce():
    print()
    print()
    print(f"{get_greeting()}, Peter.")
    identity = get_identity()

    print(f"I am {identity['name']}.")
    print(f"Version: {identity['version']}")
    print(f"Purpose: {identity['purpose']}")
    print("Current abilities:")
    print("- introduce myself")
    print()
    print("Current limitations:")
    print("- almost everything")
    print()

def main():
    import sys

    if len(sys.argv) > 1:

        command = sys.argv[1]
        argument = None

        if len(sys.argv) > 2:
            argument = sys.argv[2]

        if run(command, argument):
            return

        print(f"Unknown command: {command}")
        print("Try: alf help")
        return

    introduce()

if __name__ == "__main__":
    main()
