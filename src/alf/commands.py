"""
ALF command dispatcher.
"""

from .status import get_status_information
from .memory import remember, get_memories, get_memory_categories
from .identity import get_identity, get_about_information
from .presentation import (
    render_about,
    render_commands,
    render_memories,
    render_version,
    render_status,
    render_greeting,
    render_memory_saved,
    render_memory_usage,
    render_invalid_memory_category,
)


def status_command(argument=None):
    render_status(get_status_information())


def hello_command(argument=None):
    render_greeting()


def help_command(argument=None):
    render_commands(get_commands())


def remember_command(category=None, content=None):
    if not category or not content:
        render_memory_usage(commands["remember"]["usage"])
        return

    categories = get_memory_categories()

    if category not in categories:
        render_invalid_memory_category(category, categories)
        return

    remember(category, content)
    render_memory_saved(category)


def memories_command(argument=None):
    render_memories(get_memories())


def about_command(argument=None):
    print()

    render_about(
        get_about_information(),
        show_details=argument == "--details",
    )


def version_command(argument=None):
    render_version(get_identity())


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
