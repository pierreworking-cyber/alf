"""
ALF help system.
"""

from .presentation import info, section


def render_command_help(command_name, command):
    """
    Render help for a single command.
    """

    section(command_name)

    info(command["help"])

    section("Usage:")
    info(f"    {command['usage']}")

    if "options" in command:
        section("Options:")

        for option, description in command["options"].items():
            info(f"    {option}")
            info(f"        {description}")

    if "notes" in command:
        section("Notes:")

        for note in command["notes"]:
            info(f"    {note}")

    if "examples" in command:
        section("Examples:")

        for example in command["examples"]:
            info(f"    {example}")
