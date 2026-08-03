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

            for key, value in capability["details"].items():
                print(f"    {key}: {value}")

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
        _, created, category, content = memory

        print(f"{created} [{category}]")
        print(f"  {content}")
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
