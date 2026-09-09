"""
ALF system awareness.

Provides basic information about the machine ALF is running on.
"""

import platform
import subprocess
import time


def get_uptime():
    """Return system uptime in seconds on macOS."""
    if platform.system() != "Darwin":
        return None

    try:
        result = subprocess.run(
            ["sysctl", "-n", "kern.boottime"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None

    if result.returncode != 0:
        return None

    fields = result.stdout.strip()
    if "sec =" not in fields:
        return None

    try:
        boot_time = int(fields.split("sec =", 1)[1].split(",", 1)[0].strip())
    except (IndexError, ValueError):
        return None

    return str(time.time() - boot_time)


def get_system_information():
    """
    Return basic system information as structured data.
    """
    return {
        "operating_system": platform.system(),
        "hostname": platform.node(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "uptime": get_uptime(),
    }


def get_capability():
    """
    Return system awareness capability information.
    """
    return {
        "id": "system",
        "name": "System awareness",
        "description": "Provides basic information about the system running ALF",
    }
