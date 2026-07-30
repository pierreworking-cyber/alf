"""
ALF command dispatcher.
"""

from .system import get_system_report
from .memory import remember, get_memories, get_memory_categories
from .identity import get_identity

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
        usage = commands[command]["usage"]

        print(f"- {command}")
        print(f"    {description}")
        print(f"    Usage: {usage}")
        print()

def remember_command(category=None, content=None):
    if not category or not content:
        print()
        print(f"Usage: {commands['remember']['usage']}")
        print()
        return

    if category not in get_memory_categories():
        print()
        print(f"Unknown category: {category}")
        print()
        print("Valid categories:")

        for valid_category in get_memory_categories():
            print(f"- {valid_category}")

        print()
        return

    remember(category, content)

    print()
    print(f"I'll remember that Peter [{category}].")
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

def about_command(argument=None):

    identity = get_identity()

    print()
    print(identity["name"])
    print("---")
    print(identity["purpose"])
    print()

    print("Capabilities:")
    print("- System awareness")
    print("- Persistent memory")
    print("- Categorised knowledge storage")
    print("- Command discovery")
    print()

commands = {
    "status": {
        "function": status_command,
        "help": "Show system information.",
        "usage": "alf status",
    },

    "hello": {
        "function": hello_command,
        "help": "Show welcome message.",
        "usage": "alf hello",
    },

    "help": {
        "function": help_command,
        "help": "List available abilities.",
        "usage": "alf help",
    },

    "remember": {
        "function": remember_command,
        "help": "Add a memory.",
        "usage": 'alf remember <category> "text"',
    },

    "memories": {
        "function": memories_command,
        "help": "Recall previous memories.",
        "usage": "alf memories",
    },

    "about": {
        "function": about_command,
        "help": "Explain what ALF is.",
        "usage": "alf about",
    },
}

def run(command: str, arguments=None):

    if command in commands:

        if arguments:
            commands[command]["function"](*arguments)
        else:
            commands[command]["function"]()

        return True

    return False
