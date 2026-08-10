"""
ALF presentation helpers.
"""

from datetime import datetime

from rich.console import Console
from rich.table import Table

console = Console(markup=False)


def title(text):
    """
    Render a major ALF heading.
    """

    console.print(text, style="bold")
    console.print("─" * len(text))


def section(text):
    """
    Render a report section heading.
    """

    console.print(text)
    console.print("─" * len(text))


def success(text):
    """
    Render a successful status message.
    """

    console.print(f"✓ {text}")


def warning(text):
    """
    Render a warning message.
    """

    console.print(f"! {text}")


def error(text):
    """
    Render an error message.
    """

    console.print(f"✗ {text}")


def info(text):
    """
    Render informational text.
    """

    console.print(text)


MEMORY_CATEGORY_PRIORITY = [
    "decision",
    "preference",
    "fact",
    "note",
]


def render_greeting(greeting):
    """
    Render ALF startup greeting.
    """

    console.print()
    console.print(greeting)


def render_ready(status):
    """
    Render ALF startup summary.
    """

    identity = status["identity"]
    memory = status["memory"]
    git = status["git"]

    console.print()

    info(f"ALF {identity['version']} ready.")

    console.print()

    info(f"Memories: {memory['total_memories']}")
    info(f"Git: {git['branch']} ({git['status']})")
    info("System: OK")

    console.print()


def render_about(about, show_details=False):
    """
    Render ALF about information.

    Args:
        about: Structured ALF about information.
        show_details: Include capability detail information when available.
    """

    identity = about["identity"]

    title("ALF")

    info(f"I am {identity['name']}.")
    info(f"Version: {identity['version']}")
    info(f"Purpose: {identity['purpose']}")

    console.print()

    section("Current capabilities:")

    for capability in about["capabilities"]:
        info(f"- {capability['name']}")
        info(f"  {capability['description']}")

        if show_details and "details" in capability:
            info("  Details:")
            render_capability_details(capability)

    if about["warnings"]:
        console.print()
        info("Warnings:")

        for warning in about["warnings"]:
            error(f"- {warning}")

    console.print()

    section("Current limitations:")

    for limitation in about["limitations"]:
        info(f"- {limitation}")

    console.print()
    info("Type 'alf help' to see available commands.")


def render_commands(commands):
    """
    Render available ALF commands.
    """

    title("ALF help")
    console.print()
    section("Available commands:")

    console.print()

    for command in sorted(commands):
        description = commands[command]["help"]
        usage = commands[command]["usage"]

        info(f"- {command}")
        info(f"    {description}")
        info(f"    Usage: {usage}")
        console.print()


def render_command_help(command_name, command):
    console.print()

    title(command_name)

    console.print()

    info(command["help"])

    console.print()

    section("Usage:")
    info(f"    {command['usage']}")

    if "options" in command:
        console.print()
        info("Options:")

        for option, description in command["options"].items():
            console.print()
            info(f"    {option}")
            info(f"        {description}")

    if "notes" in command:
        console.print()
        info("Notes:")

        for note in command["notes"]:
            info(f"    {note}")

    if "examples" in command:
        console.print()
        section("Examples:")

        for example in command["examples"]:
            info(f"    {example}")


def render_memory_entry(memory):
    """
    Render a single ALF memory entry.

    The stored timestamp is converted from the database format
    into ALF's human-readable UK-style display format.
    """

    created = datetime.strptime(
        memory["created"],
        "%Y-%m-%d %H:%M:%S",
    ).strftime("%d-%b-%Y %H:%M:%S")

    info(f"(id: {memory['id']}) {created} [{memory['category']}] [{memory['status']}]")
    info(f"  {memory['content']}")
    console.print()


def render_memories(memories, options=None):
    """
    Render stored ALF memories.
    """

    title("ALF memories")

    if not memories:
        info("No memories stored.")
        return

    if options and options.get("group") == "category":
        render_grouped_memories(memories)
        return

    for memory in memories:
        render_memory_entry(memory)


def render_grouped_memories(memories):
    """
    Render ALF memories grouped by category.
    """

    grouped = {}

    for memory in memories:
        category = memory["category"]

        if category not in grouped:
            grouped[category] = []

        grouped[category].append(memory)

    for category in MEMORY_CATEGORY_PRIORITY:
        if category not in grouped:
            continue

        section(category.upper())

        for memory in grouped[category]:
            render_memory_entry(memory)


def render_version(identity):
    """
    Render ALF version information.
    """

    console.print()
    console.print(f"ALF version {identity['version']}", markup=False)
    console.print()


def render_status(status):
    """
    Render ALF status information.
    """

    identity = status["identity"]
    system = status["system"]
    memory = status["memory"]
    git = status["git"]

    title("ALF status")

    info(f"Name: {identity['name']}")
    info(f"Version: {identity['version']}")
    info(f"Purpose: {identity['purpose']}")

    console.print()

    info(f"Operating system: {system['operating_system']}")
    info(f"Hostname: {system['hostname']}")
    info(f"Python: {system['python_version']}")
    info(f"Uptime: {system['uptime']}")

    console.print()

    info(f"Git branch: {git['branch']}")
    info(f"Git status: {git['status']}")
    info(f"Last commit: {git['last_commit']}")

    console.print()

    info(f"Stored memories: {memory['total_memories']}")
    info(f"Memory categories: {', '.join(memory['categories'])}")


def render_unknown_option(option):
    """
    Render an invalid command option.
    """

    console.print(f"Unknown option: {option}")


def render_capability_details(capability):
    """
    Render capability-specific detail information.
    """

    if capability["id"] == "commands":
        commands = capability["details"]["commands"]

        for command in sorted(commands):
            info(f"    {command}")
            info(f"      {commands[command]['help']}")
            info(f"      Usage: {commands[command]['usage']}")

        return

    for key, value in capability["details"].items():
        info(f"    {key}: {value}")


def render_memory_usage(usage):
    """
    Render memory command usage.
    """

    console.print()
    info(f"Usage: {usage}")
    console.print()


def render_invalid_related_memory(memory_id, usage):
    """
    Render an invalid related memory error.
    """

    console.print()
    info(f"Related memory ID is invalid or does not exist: {memory_id}")
    console.print()
    info("Please format as follows:")
    info(f"    {usage}")
    console.print()


def render_memory(memory, related_memories=None):
    """
    Render a single ALF memory and its direct relationships.
    """

    console.print()

    if memory is None:
        info("Memory not found.")
        console.print()
        return

    render_memory_entry(memory)

    if related_memories:
        section("Related memories:")

        for related_memory in related_memories:
            render_memory_entry(related_memory)

    if memory.get("previous_memory"):
        previous = memory["previous_memory"]

        section("Previous memory:")
        render_memory_entry(previous)


def render_memory_categories(categories):
    """
    Render available ALF memory categories.
    """

    title("ALF memory categories")

    console.print()

    for category in categories:
        info(f"- {category}")

    console.print()


def render_memory_archived(memory_id):
    """
    Render archive confirmation.
    """

    console.print()
    success(f"Memory {memory_id} archived.")
    console.print()


def render_memory_saved(category):
    """
    Render memory confirmation.
    """

    console.print()
    success(f"I'll remember that Peter [{category}].")
    console.print()


def render_memory_forgotten(memory_id):
    """
    Confirm that a memory has been forgotten.
    """

    success(f"Memory {memory_id} forgotten.")


def render_memory_not_numeric():
    """
    Render invalid memory ID message.
    """

    console.print()
    error("Memory ID must be a number.")
    console.print()


def render_memory_history(history):
    """
    Render memory history chain.
    """

    console.print()

    section("Memory history")

    for memory in history:
        render_memory_entry(memory)

    console.print()


def render_memory_positive():
    """
    Render invalid positive memory ID message.
    """

    console.print()
    error("Memory IDs must be positive.")
    console.print()


def render_invalid_memory_category(category, categories):
    """
    Render invalid memory category error.
    """

    console.print()
    error(f"Unknown category: {category}")

    console.print()

    info("Valid categories:")

    for valid_category in categories:
        info(f"- {valid_category}")

    console.print()


def render_memory_help():
    """
    Render memory command help.
    """

    console.print()

    section("Usage:")
    info("    alf memories [options]")

    console.print()

    info("Options:")

    console.print()

    info("  --all")
    info("      Include archived memories.")

    console.print()

    info("  --category <name>")
    info("      Show only memories in a category.")

    console.print()

    info("  --group category")
    info("      Group memories by category.")

    console.print()


def render_health(report, show_details=False):
    """
    Render ALF health information.
    """

    checks = {
        check["name"]: check
        for check in report["checks"]
    }

    modules = checks["Modules"]["details"]
    commands = checks["Commands"]["details"]

    failed_modules = modules["failed_modules"]
    command_warnings = commands["warnings"]

    if not failed_modules and not command_warnings and not show_details:
        console.print()
        console.print("ALF health: OK")
        console.print()
        return

    if failed_modules:
        console.print()

        section("ALF health issues")

        error("Failed modules:")

        for failure in failed_modules:
            error(f"- {failure['module'].removeprefix('alf.')}")
            error(f"  {failure['error']}")

        console.print()

    if command_warnings:
        console.print()

        error("Command integrity issues:")

        for warning in command_warnings:
            error(f"- {warning['command']}")
            error(f"  {warning['message']}")

        console.print()

    if show_details:
        console.print()
        console.print("ALF health details")
        console.print()

        table = Table(
            title="Module status",
        )

        table.add_column("Module")
        table.add_column("Status")

        for module in modules["advertising_modules"]:
            table.add_row(
                module.removeprefix("alf."),
                "capability reporting",
            )

        for module in modules["non_reporting_modules"]:
            table.add_row(
                module.removeprefix("alf."),
                "non-reporting",
            )

        console.print(table)
        console.print()

        console.print()

        table = Table(
            title="Command integrity",
        )

        table.add_column("Check")
        table.add_column("Status")

        table.add_row(
            "Catalogue ↔ handlers",
            "OK" if not command_warnings else "issues found",
        )

        console.print(table)
        console.print()
