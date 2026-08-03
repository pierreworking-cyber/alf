"""
ALF presentation helpers.
"""


def render_about(about, show_details=False):
    """
    Render ALF about information.

    Args:
        about: Structured ALF about information.
        show_details: Include capability detail information when available.
    """

    identity = about["identity"]

    print(f"I am {identity['name']}.")
    print(f"Version: {identity['version']}")
    print(f"Purpose: {identity['purpose']}")

    print()
    print("Current capabilities:")

    for capability in about["capabilities"]:
        print(f"- {capability['name']}")
        print(f"  {capability['description']}")

        if show_details and "details" in capability:
            print("  Details:")

            for key, value in capability["details"].items():
                print(f"    {key}: {value}")

    if about["warnings"]:
        print()
        print("Warnings:")

        for warning in about["warnings"]:
            print(f"- {warning}")

    print()
    print("Current limitations:")

    for limitation in about["limitations"]:
        print(f"- {limitation}")

    print()
