"""
ALF help system.
"""


def render_command_help(command_name, command):
    print()

    print(command_name)
    print("-" * len(command_name))

    print()

    print(command["help"])

    print()

    print("Usage:")
    print(f"    {command['usage']}")

    if "options" in command:
        print()
        print("Options:")

        for option, description in command["options"].items():
            print()
            print(f"    {option}")
            print(f"        {description}")

    print()

    if "examples" in command:
        print()
        print("Examples:")

        for example in command["examples"]:
            print()
            print(f"    {example}")
