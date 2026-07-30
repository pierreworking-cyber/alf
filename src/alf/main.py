#!/usr/bin/env python3

"""
ALF - Peter's local computing companion.

Version 0.1
"""

from .system import get_system_report

VERSION = "0.1"


def introduce():
    print()
    print("Good evening, Peter.")
    print()
    print("I am ALF.")
    print(f"Version: {VERSION}")
    print()
    print("Current abilities:")
    print("- introduce myself")
    print()
    print("Current limitations:")
    print("- almost everything")
    print()


def main():
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "status":
            print()
            print(get_system_report())
            print()
            return

    introduce()


if __name__ == "__main__":
    main()
