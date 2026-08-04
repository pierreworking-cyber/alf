"""
ALF presentation helpers.
"""


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


def render_memories(memories):
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

    for memory in memories:
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


def render_memory_saved(category):
    """
    Render memory confirmation.
    """

    print()
    print(f"I'll remember that Peter [{category}].")
    print()


def render_memory_usage(usage):
    """
    Render memory command usage.
    """

    print()
    print(f"Usage: {usage}")
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
