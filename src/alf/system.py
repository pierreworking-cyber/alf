"""
ALF system awareness.

Provides information about the machine ALF is running on.
"""

import platform
import os


def get_system_report():
    report = []

    report.append("ALF system report")
    report.append("-----------------")

    report.append(f"Operating system: {platform.system()}")
    report.append(f"Hostname: {platform.node()}")
    report.append(f"Architecture: {platform.machine()}")

    cpu = platform.processor()
    if cpu:
        report.append(f"Processor: {cpu}")

    report.append(f"Python version: {platform.python_version()}")

    memory = get_memory()

    if memory:
        report.append(f"Memory: {memory}")

    return "\n".join(report)


def get_memory():
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
