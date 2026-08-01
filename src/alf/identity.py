"""
ALF identity management.
"""

import tomllib
from .paths import get_data_directory


def get_identity():
    identity_file = get_data_directory() / "identity.toml"

    with open(identity_file, "rb") as file:
        return tomllib.load(file)

def describe_identity():
    identity = get_identity()

    print(f"I am {identity['name']}.")
    print(f"Version: {identity['version']}")
    print(f"Purpose: {identity['purpose']}")

    print()
    print("Current capabilities:")

    for capability in identity["capabilities"]:
        print(f"- {capability}")

    print()
    print("Current limitations:")

    for limitation in identity["limitations"]:
        print(f"- {limitation}")

    print()
