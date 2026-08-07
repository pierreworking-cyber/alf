"""
ALF command dispatcher.
"""

from .command_catalogue import commands
from .healthcheck import get_health_report
from .help import render_command_help
from .identity import (
    get_about_information,
    get_identity,
)
from .memory import (
    archive_memory,
    get_memories,
    get_memory,
    get_memory_categories,
    get_memory_history,
    get_memory_query_options,
    remember,
    search_memories,
)
from .presentation import (
    render_about,
    render_commands,
    render_greeting,
    render_health,
    render_invalid_memory_category,
    render_memories,
    render_memory,
    render_memory_archived,
    render_memory_categories,
    render_memory_history,
    render_memory_not_numeric,
    render_memory_positive,
    render_memory_saved,
    render_memory_usage,
    render_status,
    render_version,
)
from .status import get_status_information

REQUIRED_COMMAND_FIELDS = [
    "id",
    "help",
    "usage",
]


def health_command(argument=None):
    render_health(
        get_health_report(),
        show_details=argument == "--details",
    )


def status_command(argument=None):
    print(render_status(get_status_information()))


def hello_command(argument=None):
    render_greeting()


def help_command(argument=None):
    if argument and argument in commands:
        render_command_help(argument, commands[argument])
        return

    render_commands(get_commands())


def remember_command(category=None, content=None):
    if not category or not content or not content.strip():
        render_memory_usage(commands["remember"]["usage"])
        return

    categories = get_memory_categories()

    if category not in categories:
        render_invalid_memory_category(category, categories)
        return

    content = content.strip()
    remember(category, content)
    render_memory_saved(category)


def parse_memory_query_options(arguments):
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
            return None

        index += 1

    return options


def memories_command(*arguments):
    options = parse_memory_query_options(arguments)

    if options is None:
        return

    memories = get_memories(options)

    render_memories(memories, options)


def search_command(*arguments):
    if not arguments:
        render_memory_usage(commands["search"]["usage"])
        return

    term = arguments[0]

    options = parse_memory_query_options(arguments[1:])

    if options is None:
        return

    memories = search_memories(term, options)

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


def history_command(*arguments):
    if len(arguments) != 1:
        render_memory_usage(commands["history"]["usage"])
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

    history = get_memory_history(memory_id)

    if not history:
        render_memory(None)
        return

    render_memory_history(history)


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


command_handlers = {
    "status": status_command,
    "hello": hello_command,
    "help": help_command,
    "remember": remember_command,
    "memories": memories_command,
    "categories": categories_command,
    "memory": memory_command,
    "history": history_command,
    "health": health_command,
    "about": about_command,
    "archive": archive_command,
    "version": version_command,
    "search": search_command,
}


def run(command: str, arguments=None):

    if command in command_handlers:
        if arguments:
            command_handlers[command](*arguments)
        else:
            command_handlers[command]()

        return True

    return False


def validate_commands():
    """
    Validate command metadata.
    """

    warnings = []
    command_ids = set()

    for name, command in commands.items():
        for field in REQUIRED_COMMAND_FIELDS:
            if field not in command:
                warnings.append(
                    {
                        "command": name,
                        "message": f"Command has no {field}",
                    }
                )

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
        catalog[name] = command.copy()

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
