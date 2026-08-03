"""
ALF identity management.
"""

import tomllib
from .paths import get_data_directory
from .capabilities import discover_capabilities


def get_identity():
    identity_file = get_data_directory() / "identity.toml"

    with open(identity_file, "rb") as file:
        return tomllib.load(file)


def get_about_information():
    """
    Return ALF about information as structured data.
    """
    identity = get_identity()
    report = discover_capabilities()

    return {
        "identity": identity,
        "capabilities": report["capabilities"],
        "warnings": report["warnings"],
        "limitations": identity["limitations"],
    }


def describe_identity():
    about = get_about_information()

    identity = about["identity"]

    print(f"I am {identity['name']}.")
    print(f"Version: {identity['version']}")
    print(f"Purpose: {identity['purpose']}")

    print()
    print("Current capabilities:")

    for capability in about["capabilities"]:
        print(f"- {capability['name']}")
        print(f"  {capability['description']}")

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
