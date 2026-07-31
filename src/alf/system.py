"""
ALF system awareness.

Provides information about the machine ALF is running on.
"""

import platform
import os
from .git import get_git_branch

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
    report = []

    report.append("ALF system report")
    report.append("-----------------")

    report.append(f"Operating system: {platform.system()}")
    report.append(f"Hostname: {platform.node()}")
    report.append(f"Architecture: {platform.machine()}")
    report.append(f"Uptime: {get_uptime()}")

    cpu = platform.processor()
    if cpu:
        report.append(f"Processor: {cpu}")

    report.append(f"Python version: {platform.python_version()}")
    report.append(f"Git branch: {get_git_branch()}")

    total_memory = get_total_memory()
    available_memory = get_available_memory()

    if total_memory:
        report.append(f"Total memory: {total_memory}")

    if available_memory:
        report.append(f"Available memory: {available_memory}")

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
