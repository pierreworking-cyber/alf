"""
ALF self-awareness.

Combines information from ALF's various capabilities.
"""


from .identity import get_identity
from .system import get_system_information
from .memory import get_memory_information
from .git import get_git_information

def get_status_information():
    """
    Return ALF status as structured data.
    """

    status = {}

    status["identity"] = get_identity()
    status["system"] = get_system_information()
    status["memory"] = get_memory_information()
    status["git"] = get_git_information()

    return status

def get_status_report():
    """
    Return a human-readable ALF status report.
    """

    status = get_status_information()

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
    report.append(
        f"Memory categories: {', '.join(memory['categories'])}"
    )

    return "\n".join(report)
