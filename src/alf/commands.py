"""
ALF command dispatcher.
"""

from .system import get_system_report
from .memory import remember, get_memories


def status_command(argument=None):
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

def remember_command(text):
    remember("note", text)

    print()
    print("Memory stored.")
    print()


def memories_command():
    memories = get_memories()

    print()
    print("ALF memories:")
    print()

    for memory in memories:
        print(memory)

    print()

commands = {
    "status": status_command,
    "hello" : hello_command,
    "help" : help_command,
    "remember" : remember_command,
    "memories" : memories_command,
}

def run(command: str, argument=None):
    """
    Execute an ALF command.

    Returns True if the command was recognised.
    """

    if command in commands:
        commands[command](argument)
        return True

    return False
