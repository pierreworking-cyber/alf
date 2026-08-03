"""
ALF system awareness.

Provides information about the machine ALF is running on.
"""

import platform


def get_uptime():
    """
    Return system uptime as a friendly string.
    """

    with open("/proc/uptime") as f:
        seconds = float(f.read().split()[0])

    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)

    return f"{days} days, {hours} hours"


def get_total_memory():
    """
    Return total memory if available.
    Linux implementation.
    """

    try:
        with open("/proc/meminfo") as file:
            for line in file:
                if line.startswith("MemTotal"):
                    kb = int(line.split()[1])
                    gb = kb / 1024 / 1024
                    return f"{gb:.1f} GB"

    except Exception:
        pass

    return None


def get_system_information():
    """
    Return system information as structured data.
    """

    information = {}

    information["operating_system"] = platform.system()
    information["hostname"] = platform.node()
    information["architecture"] = platform.machine()
    information["python_version"] = platform.python_version()

    information["uptime"] = get_uptime()

    information["total_memory"] = get_total_memory()
    information["available_memory"] = get_available_memory()

    return information


def get_capability():
    """
    Return system awareness capability information.
    """

    return {
        "id": "system",
        "name": "System awareness",
        "description": "Reports information about the machine ALF is running on",
    }
