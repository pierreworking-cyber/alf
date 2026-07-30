"""
ALF diary system.

Stores events and notes about ALF's journey.
"""

from datetime import datetime
from pathlib import Path


DIARY_FILE = Path("logs/diary.md")


def write_entry(message: str):
    """
    Add an entry to ALF's diary.
    """

    date = datetime.now().strftime("%d %B %Y")

    entry = f"""
## {date}

{message}

"""

    DIARY_FILE.parent.mkdir(exist_ok=True)

    with open(DIARY_FILE, "a") as file:
        file.write(entry)


def read_diary():
    """
    Return the contents of ALF's diary.
    """

    if not DIARY_FILE.exists():
        return "ALF's diary is empty."

    return DIARY_FILE.read_text()
