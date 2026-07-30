#!/usr/bin/env python3

"""
ALF - Peter's local computing companion.

"""

from .identity import get_identity
from .commands import run

def introduce():
    print()
    print("Good evening, Peter.")
    print()
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
        if run(sys.argv[1]):
            return

        print(f"Unknown command: {sys.argv[1]}")
        print("Try: alf help")
        return

    introduce()


if __name__ == "__main__":
    main()
