"""
ALF presentation helpers.
"""

MEMORY_CATEGORY_PRIORITY = [
    "decision",
    "preference",
    "fact",
    "note",
]


def render_about(about, show_details=False):
    """
    Render ALF about information.

    Args:
        about: Structured ALF about information.
        show_details: Include capability detail information when available.
    """

    identity = about["identity"]

    print(f"I am {identity['name']}.")
    print(f"Version: {identity['version']}")
    print(f"Purpose: {identity['purpose']}")

    print()
    print("Current capabilities:")

    for capability in about["capabilities"]:
        print(f"- {capability['name']}")
        print(f"  {capability['description']}")

        if show_details and "details" in capability:
            print("  Details:")
            render_capability_details(capability)

        if about["warnings"]:
            print()
            print("Warnings:")

            for warning in about["warnings"]:
                print(f"- {warning}")

    print()
    print("Current limitations:")

    for limitation in about["limitations"]:
        print(f"- {limitation}")

    print()


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
    report = []

    report.append("ALF status")
    report.append("----------")

    identity = status["identity"]
    system = status["system"]
    memory = status["memory"]
    git = status["git"]

    report.append(f"Name: {identity['name']}")
    report.append(f"Version: {identity['version']}")
    report.append(f"Purpose: {identity['purpose']}")
    report.append("")

    report.append(f"Operating system: {system['operating_system']}")
    report.append(f"Hostname: {system['hostname']}")
    report.append(f"Python: {system['python_version']}")
    report.append(f"Uptime: {system['uptime']}")
    report.append("")
    report.append(f"Git branch: {git['branch']}")
    report.append(f"Git status: {git['status']}")
    report.append(f"Last commit: {git['last_commit']}")
    report.append("")
    report.append(f"Stored memories: {memory['total_memories']}")
    report.append(f"Memory categories: {', '.join(memory['categories'])}")

    return "\n".join(report)


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


def render_greeting():
    """
    Render ALF greeting.
    """

    print()
    print("Hello Peter.")
    print()


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
