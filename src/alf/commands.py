"""
ALF command dispatcher.
"""

from .answer import prepare_answer
from .calc import CalculationError, calculate
from .command_catalogue import commands
from .command_resolution import resolve_category, resolve_command
from .healthcheck import get_health_report
from .identity import get_about_information, get_identity
from .llm import evaluate_research
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
    render_command_structure_error,
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
from .research import research_web, research_wikipedia_candidates
from .status import get_status_information


def run(command: str, arguments=None):
    """
    Route a user command through deterministic command resolution.

    The resolver permits exact command names and unambiguous leading
    prefixes, but does not infer natural-language intent.
    """

    command = resolve_command(command)

    if command is None:
        return False

    if arguments:
        command_handlers[command](*arguments)
    else:
        command_handlers[command]()

    return True


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
    category = None
    content = None
    related_memory_ids = None
    index = 0

    while index < len(arguments):
        argument = arguments[index]

        if argument in ("-c", "--category"):
            if category is not None or index + 1 >= len(arguments):
                render_command_structure_error("remember")
                return

            category = arguments[index + 1]
            index += 2
            continue

        if argument in ("-r", "--relate"):
            if (
                related_memory_ids is not None
                or index + 1 >= len(arguments)
            ):
                render_command_structure_error("remember")
                return

            related_memory_ids = arguments[index + 1]
            index += 2
            continue

        if argument.startswith("-"):
            render_command_structure_error("remember")
            return

        if category is None:
            category = argument
        elif content is None:
            content = argument
        else:
            render_command_structure_error("remember")
            return

        index += 1

    if category is None or content is None:
        render_command_structure_error("remember")
        return

    category = resolve_category(category)

    if category is None:
        render_invalid_memory_category(
            arguments[0],
            get_memory_categories(),
        )
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

    candidates = research_wikipedia_candidates(question)
    evaluation = evaluate_research(question, candidates)

    if evaluation["relevant"]:
        relevant_candidates = [
            candidates[index - 1]
            for index in evaluation["candidates"]
            if 1 <= index <= len(candidates)
        ]

        if relevant_candidates:
            answer = prepare_answer(
                question,
                [relevant_candidates[0]],
            )
            render_question(answer)
            return

    web_candidates = research_web(question)
    web_evaluation = evaluate_research(question, web_candidates)

    if web_evaluation["relevant"]:
        relevant_candidates = [
            web_candidates[index - 1]
            for index in web_evaluation["candidates"]
            if 1 <= index <= len(web_candidates)
        ]

        if relevant_candidates:
            answer = prepare_answer(
                question,
                [relevant_candidates[0]],
            )
            render_question(answer)
            return

    render_question(
        "I couldn't find reliable research that answers your question. "
        "I don't want to guess."
    )


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
