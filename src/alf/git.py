"""
Git repository awareness.
"""

import subprocess


def get_git_branch():
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True,
        text=True,
    )

    return result.stdout.strip()

def get_git_status():
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
    )

    if result.stdout.strip():
        return "modified"

    return "clean"

def get_last_commit():
    result = subprocess.run(
        ["git", "log", "-1", "--pretty=%s"],
        capture_output=True,
        text=True,
    )

    return result.stdout.strip()
