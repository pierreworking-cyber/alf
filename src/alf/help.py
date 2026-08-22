"""
Help rendering for ALF commands.

Builds human-readable command help from the metadata in the command
catalogue and passes the formatted sections to ALF's presentation layer.
"""

from .presentation import info, section


def render_command_help(command_name, command):
    """
    Render help for a single ALF command.

    The command metadata determines which sections are displayed,
    including usage, options, notes, and examples. Presentation is
    delegated to the shared output functions.

    Args:
        command_name: The public name of the command.
        command: The command metadata from the command catalogue.
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
