"""
ALF command dispatcher.
"""

from .status import get_status_report
from .memory import remember, get_memories, get_memory_categories
from .identity import get_identity, get_about_information
from .presentation import render_about, render_commands, render_memories


def status_command(argument=None):
    print()
    print(get_status_report())
    print()


def hello_command(argument=None):
    print()
    print("Hello Peter.")
    print()


def help_command(argument=None):
    render_commands(get_commands())


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
    render_memories(get_memories())


def about_command(argument=None):
    print()

    render_about(
        get_about_information(),
        show_details=argument == "--details",
    )


def version_command(argument=None):
    identity = get_identity()

    print()
    print(f"ALF version {identity['version']}")
    print()


commands = {
    "status": {
        "id": "system.status",
        "function": status_command,
        "help": "Show system information.",
        "usage": "alf status",
    },
    "hello": {
        "id": "identity.greeting",
        "function": hello_command,
        "help": "Show welcome message.",
        "usage": "alf hello",
    },
    "help": {
        "id": "command.list",
        "function": help_command,
        "help": "List available commands.",
        "usage": "alf help",
    },
    "remember": {
        "id": "memory.add",
        "function": remember_command,
        "help": "Add a memory.",
        "usage": 'alf remember <category> "text"',
    },
    "memories": {
        "id": "memory.list",
        "function": memories_command,
        "help": "Recall previous memories.",
        "usage": "alf memories",
    },
    "about": {
        "id": "identity.about",
        "function": about_command,
        "help": "Explain what ALF is.",
        "usage": "alf about [--details]",
    },
    "version": {
        "id": "identity.version",
        "function": version_command,
        "help": "Show ALF version.",
        "usage": "alf version",
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


def validate_commands():
    """
    Validate command metadata.
    """

    warnings = []
    command_ids = set()

    for name, command in commands.items():
        command_id = command.get("id")

        if not command_id:
            warnings.append(
                {
                    "command": name,
                    "message": "Command has no id",
                }
            )
            continue

        if command_id in command_ids:
            warnings.append(
                {
                    "command": name,
                    "message": f"Duplicate command id: {command_id}",
                }
            )
            continue

        command_ids.add(command_id)

    return warnings


def get_commands():
    """
    Return public command information.
    """
    catalog = {}

    for name, command in commands.items():
        catalog[name] = {
            key: value for key, value in command.items() if key != "function"
        }

    return catalog


def get_capability():
    """
    Return command discovery capability information.
    """

    return {
        "id": "commands",
        "name": "Command discovery",
        "description": "Reports available ALF commands",
        "details": {
            "commands": get_commands(),
            "warnings": validate_commands(),
        },
    }
