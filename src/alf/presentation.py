"""
ALF presentation helpers.
"""

from rich.console import Console
from rich.table import Table

console = Console()


def title(text):
    """
    Render a section title.
    """

    line = "─" * (len(text) + 10)
    console.print(f"{line} {text} {line}")


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


def render_ready(status):
    """
    Render ALF startup summary.
    """

    identity = status["identity"]
    memory = status["memory"]
    git = status["git"]

    print()
    print(f"ALF {identity['version']} ready.")
    print()
    print(f"Memories: {memory['total_memories']}")
    print(f"Git: {git['branch']} ({git['status']})")
    print("System: OK")
    print()


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

    info("Current capabilities:")

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

    info("Current limitations:")

    for limitation in about["limitations"]:
        info(f"- {limitation}")

    console.print()
    info("Type 'alf help' to see available commands.")


def render_commands(commands):
    """
    Render available ALF commands.
    """

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


def render_memories(memories, options=None):
    """
    Render stored ALF memories.
    """

    print()
    print("ALF memories")
    print("------------")

    if not memories:
        print("No memories stored.")
        print()
        return

    if options and options.get("group") == "category":
        render_grouped_memories(memories)
        return

    for memory in memories:
        print(
            f"(id: {memory['id']}) {memory['created']} "
            f"[{memory['category']}] [{memory['status']}]"
        )
        print(f"  {memory['content']}")
        print()


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

        print()
        print(category.upper())
        print("-" * len(category))

        for memory in grouped[category]:
            print(
                f"(id: {memory['id']}) {memory['created']} "
                f"[{memory['category']}] [{memory['status']}]"
            )
            print(f"  {memory['content']}")
            print()


def render_version(identity):
    """
    Render ALF version information.
    """

    print()
    print(f"ALF version {identity['version']}")
    print()


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


def render_capability_details(capability):
    """
    Render capability-specific detail information.
    """
    if capability["id"] == "commands":
        commands = capability["details"]["commands"]

        for command in sorted(commands):
            print(f"    {command}")
            print(f"      {commands[command]['help']}")
            print(f"      Usage: {commands[command]['usage']}")

        return

    for key, value in capability["details"].items():
        print(f"    {key}: {value}")


def render_memory_usage(usage):
    """
    Render memory command usage.
    """

    print()
    print(f"Usage: {usage}")
    print()


def render_memory(memory):
    """
    Render a single ALF memory.
    """

    print()

    if memory is None:
        print("Memory not found.")
        print()
        return

    print(
        f"(id: {memory['id']}) {memory['created']} "
        f"[{memory['category']}] [{memory['status']}]"
    )
    print(f"  {memory['content']}")

    if memory.get("previous_memory"):
        previous = memory["previous_memory"]

        print()
        print("Previous memory:")
        print(
            f"(id: {previous['id']}) {previous['created']} "
            f"[{previous['category']}] [{previous['status']}]"
        )
        print(f"  {previous['content']}")
    print()


def render_memory_categories(categories):
    """
    Render available ALF memory categories.
    """

    print()
    print("ALF memory categories")
    print("---------------------")

    for category in categories:
        print(f"- {category}")

    print()


def render_memory_saved(category):
    """
    Render memory confirmation.
    """

    print()
    print(f"I'll remember that Peter [{category}].")
    print()


def render_memory_archived(memory_id):
    """
    Render archive confirmation.
    """

    print()
    print(f"Memory {memory_id} archived.")
    print()


def render_memory_not_numeric():
    """
    Render invalid memory ID message.
    """

    print()
    print("Memory ID must be a number.")
    print()


def render_memory_history(history):
    """
    Render memory history chain.
    """

    print()
    print("Memory history")
    print("--------------")

    for memory in history:
        print()
        print(
            f"(id: {memory['id']}) {memory['created']} "
            f"[{memory['category']}] [{memory['status']}]"
        )
        print(f"  {memory['content']}")

    print()


def render_memory_positive():
    """
    Render invalid positive memory ID message.
    """

    print()
    print("Memory IDs must be positive.")
    print()


def render_invalid_memory_category(category, categories):
    """
    Render invalid memory category error.
    """

    print()
    print(f"Unknown category: {category}")
    print()
    print("Valid categories:")

    for valid_category in categories:
        print(f"- {valid_category}")

    print()


def render_memory_help():
    """
    Render memory command help.
    """

    print()
    print("Usage: alf memories [options]")
    print()
    print("Options:")
    print()
    print("  --all")
    print("      Include archived memories.")
    print()
    print("  --category <name>")
    print("      Show only memories in a category.")
    print()
    print("  --group category")
    print("      Group memories by category.")
    print()


def render_health(report, show_details=False):
    """
    Render ALF health information.
    """

    modules = report["checks"][0]["details"]

    failed_modules = modules["failed_modules"]

    if not failed_modules and not show_details:
        console.print()
        console.print("ALF health: OK")
        console.print()
        return

    if failed_modules:
        print()
        print("ALF health issues")
        print("-----------------")
        print()

        print("Failed modules:")

        for failure in failed_modules:
            print(f"- {failure['module'].removeprefix('alf.')}")
            print(f"  {failure['error']}")

        print()

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
