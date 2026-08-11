"""
ALF command dispatcher.
"""

from .calc import CalculationError, calculate
from .command_catalogue import commands
from .healthcheck import get_health_report
from .identity import (
    get_about_information,
    get_identity,
)
from .llm import ask
from .memory import (
    archive_memory,
    forget_memory,
    get_memories,
    get_memory,
    get_memory_categories,
    get_memory_history,
    get_memory_query_options,
    get_related_memories,
    remember,
    search_memories,
)
from .presentation import (
    render_about,
    render_calculation,
    render_calculation_error,
    render_command_help,
    render_commands,
    render_health,
    render_invalid_memory_category,
    render_invalid_related_memory,
    render_memories,
    render_memory,
    render_memory_archived,
    render_memory_categories,
    render_memory_forgotten,
    render_memory_history,
    render_memory_not_numeric,
    render_memory_positive,
    render_memory_saved,
    render_memory_usage,
    render_question,
    render_status,
    render_unknown_option,
    render_version,
)
from .research import research_wikipedia
from .status import get_status_information


def run(command: str, arguments=None):
    """
    Route a command name and its arguments to the appropriate handler.

    This is the entry point to ALF's command layer. The command handlers
    themselves deal with the work; this function is responsible only for
    dispatching the request to the right handler.
    """

    if command in command_handlers:
        if arguments:
            command_handlers[command](*arguments)
        else:
            command_handlers[command]()

        return True

    return False


def calc_command(*arguments):
    """
    Calculate a mathematical expression.
    """

    if not arguments:
        render_memory_usage(commands["calc"]["usage"])
        return

    expression = " ".join(arguments)

    try:
        result = calculate(expression)
    except CalculationError as error:
        render_calculation_error(error)
        return

    render_calculation(result)


def health_command(argument=None):
    render_health(
        get_health_report(),
        show_details=argument == "--details",
    )


def show_status():
    render_status(get_status_information())


def help_command(argument=None):
    if argument and argument in commands:
        render_command_help(argument, commands[argument])
        return

    render_commands(get_commands())


def remember_command(*arguments):
    if len(arguments) < 2:
        render_memory_usage(commands["remember"]["usage"])
        return

    category = arguments[0]
    content = arguments[1]

    related_memory_ids = None

    if len(arguments) > 2:
        if arguments[2] != "--relate" or len(arguments) != 4:
            render_memory_usage(commands["remember"]["usage"])
            return

        related_memory_ids = arguments[3]

    categories = get_memory_categories()

    if category not in categories:
        render_invalid_memory_category(category, categories)
        return

    content = content.strip()
    result = remember(
        category,
        content,
        related_memory_ids=related_memory_ids,
    )

    if result is not True:
        render_invalid_related_memory(
            related_memory_ids,
            commands["remember"]["usage"],
        )
        return

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
            render_unknown_option(argument)
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

    memory = get_memory(memory_id)
    related_memories = get_related_memories(memory_id)

    render_memory(
        memory,
        related_memories=related_memories,
    )


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


def forget_command(memory_id=None):
    if not memory_id:
        render_memory_usage(commands["forget"]["usage"])
        return

    try:
        memory_id = int(memory_id)

    except ValueError:
        render_memory_not_numeric()
        return

    if memory_id <= 0:
        render_memory_positive()
        return

    forget_memory(memory_id)
    render_memory_forgotten(memory_id)


def question_command(*arguments):
    if not arguments:
        render_memory_usage(commands["question"]["usage"])
        return

    question = " ".join(arguments).strip()
    research = research_wikipedia(question)
    answer = ask(question, research)

    render_question(answer)


def about_command(argument=None):

    render_about(
        get_about_information(),
        show_details=argument == "--details",
    )


def version_command(argument=None):
    render_version(get_identity())


# Routing table: maps user-facing command names to their handler functions.
# `run()` uses this table to dispatch each command without knowing
# how the individual command is implemented.
command_handlers = {
    "help": help_command,
    "remember": remember_command,
    "memories": memories_command,
    "categories": categories_command,
    "memory": memory_command,
    "history": history_command,
    "health": health_command,
    "about": about_command,
    "archive": archive_command,
    "forget": forget_command,
    "version": version_command,
    "calc": calc_command,
    "search": search_command,
    "question": question_command,
}


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
        },
    }
