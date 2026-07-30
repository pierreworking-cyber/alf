"""
ALF command dispatcher.
"""

from .system import get_system_report
from .memory import remember, get_memories


def status_command(argument=None):
    print()
    print(get_system_report())
    print()

def hello_command(argument=None):
    print()
    print("Hello Peter.")
    print()


def help_command(argument=None):
    print()
    print("Available commands:")
    print()

    for command in sorted(commands):
        description = commands[command]["help"]
        print(f"- {command}: {description}")
    print()

def remember_command(argument=None):
    if not argument:
        print()
        print("Usage: alf remember <text>")
        print()
        return

    remember("note", argument)

    print()
    print("I'll remember that Peter.")
    print()


def memories_command(argument=None):
    memories = get_memories()

    print()
    print("ALF memories")
    print("------------")

    if not memories:
        print("No memories stored.")
        print()
        return

    for memory in memories:
        _, created, category, content = memory

        print(f"{created} [{category}]")
        print(f"  {content}")
        print()


commands = {
    "status": {
        "function": status_command,
        "help": "Show system information."},

    "hello": {
        "function": hello_command,
        "help": "Show welcome message."},

    "help": {
        "function": help_command,
        "help": "list available abilities."},

    "remember": {
        "function": remember_command,
        "help": "Add a memory."},

    "memories":{
        "function": memories_command,
        "help": "Recall previous memories."},
}

def run(command: str, argument=None):
    """
    Execute an ALF command.

    Returns True if the command was recognised.
    """

    if command in commands:
        commands[command]["function"](argument)
        return True

    return False
