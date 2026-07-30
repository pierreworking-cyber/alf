"""
ALF command dispatcher.
"""

from .system import get_system_report


def status_command():
    print()
    print(get_system_report())
    print()

def hello_command():
    print()
    print("Hello Peter.")
    print()

def help_command():
    print()
    print("Available commands:")

    for command in sorted(commands):
        print(f"- {command}")

    print()

commands = {
    "status": status_command,
    "hello" : hello_command,
    "help" : help_command
}


def run(command: str):
    """
    Execute an ALF command.

    Returns True if the command was recognised.
    """

    if command in commands:
        commands[command]()
        return True

    return False
