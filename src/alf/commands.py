"""
ALF command dispatcher.
"""

from .status import get_status_information
from .memory import (
    remember,
    get_memories,
    get_memory_categories,
    get_memory,
    archive_memory,
    get_memory_query_options,
)
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
    render_memory_not_numeric,
    render_memory_positive,
    render_invalid_memory_category,
    render_memory,
    render_memory_categories,
    render_memory_archived,
)


def status_command(argument=None):
    print(render_status(get_status_information()))


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


def memories_command(*arguments):
    options = get_memory_query_options()

    index = 0

    while index < len(arguments):
        argument = arguments[index]

        if argument == "--all":
            options["include_archived"] = True

        elif argument == "--category":
            index += 1
            if index < len(arguments):
                options["category"] = arguments[index]

        elif argument == "--group":
            index += 1
            if index < len(arguments):
                options["group"] = arguments[index]

        else:
            print(f"Unknown option: {argument}")
            return

        index += 1

    memories = get_memories(options)
    render_memories(memories, options)


def categories_command(argument=None):
    render_memory_categories(get_memory_categories())


def memory_command(*arguments):

    if len(arguments) != 1:
        render_memory_usage(commands["memory"]["usage"])
        return

    memory_id = arguments[0]

    try:
        memory_id = int(memory_id)

    except ValueError:
        render_memory_not_numeric()
        return

    if memory_id <= 0:
        render_memory_positive()
        return

    render_memory(get_memory(memory_id))


def archive_command(memory_id=None):
    if not memory_id:
        render_memory_usage(commands["archive"]["usage"])
        return

    try:
        memory_id = int(memory_id)
    except ValueError:
        render_memory_not_numeric()
        return

    if memory_id <= 0:
        render_memory_positive()
        return

    archive_memory(memory_id)
    render_memory_archived(memory_id)


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
    "categories": {
        "id": "memory.categories",
        "function": categories_command,
        "help": "Show memory categories.",
        "usage": "alf categories",
    },
    "memory": {
        "id": "memory.show",
        "function": memory_command,
        "help": "Show a single memory.",
        "usage": "alf memory <id>",
    },
    "about": {
        "id": "identity.about",
        "function": about_command,
        "help": "Explain what ALF is.",
        "usage": "alf about [--details]",
    },
    "archive": {
        "id": "memory.archive",
        "function": archive_command,
        "help": "Archive a memory.",
        "usage": "alf archive <id>",
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
