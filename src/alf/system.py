"""
ALF system awareness.

Provides information about the machine ALF is running on.
"""

import platform

SYSTEM_INTERFACES = {
    "proc_meminfo": "/proc/meminfo",
    "proc_uptime": "/proc/uptime",
}


def read_system_value(interface, key):
    """Read a named value from a key/value system interface."""
    data = read_system_interface(interface)

    if data is None:
        return None

    for line in data.splitlines():
        name, separator, value = line.partition(":")

        if separator and name.strip() == key:
            return value.strip()

    return None


def read_system_interface(name):
    """Read a permitted system interface."""
    path = SYSTEM_INTERFACES.get(name)

    if path is None:
        return None

    try:
        with open(path) as file:
            return file.read()

    except OSError:
        return None


def read_system_field(interface, index):
    """Read a positional field from a system interface."""
    data = read_system_interface(interface)

    if data is None:
        return None

    fields = data.split()

    try:
        return fields[index]
    except IndexError:
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

    information["uptime"] = read_system_field(
        "proc_uptime",
        0,
    )

    information["total_memory"] = read_system_value(
        "proc_meminfo",
        "MemTotal",
    )
    information["available_memory"] = read_system_value(
        "proc_meminfo",
        "MemAvailable",
    )

    return information


def get_capability():
    """
    Return system awareness capability information.
    """

    return {
        "id": "system",
        "name": "System awareness",
        "description": "Provides controlled access to permitted system interfaces",
        "interfaces": list(SYSTEM_INTERFACES),
    }
