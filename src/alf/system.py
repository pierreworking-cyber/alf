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


def get_system_report():

    information = get_system_information()

    report = []

    report.append("ALF system report")
    report.append("-----------------")
    report.append(f"Operating system: {information['operating_system']}")
    report.append(f"Hostname: {information['hostname']}")
    report.append(f"Architecture: {information['architecture']}")
    report.append(f"Python version: {information['python_version']}")
    report.append(f"Uptime: {information['uptime']}")

    if information["total_memory"]:
        report.append(f"Total memory: {information['total_memory']}")

    if information["available_memory"]:
        report.append(f"Available memory: {information['available_memory']}")
    return "\n".join(report)

def get_available_memory():
    """
    Return available memory if available.
    Linux implementation.
    """

    try:
        with open("/proc/meminfo") as file:
            for line in file:
                if line.startswith("MemAvailable"):
                    kb = int(line.split()[1])
                    gb = kb / 1024 / 1024
                    return f"{gb:.1f} GB"

    except Exception:
        pass
    return None

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
