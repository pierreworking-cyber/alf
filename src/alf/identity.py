"""
ALF identity management.
"""

from pathlib import Path
import tomllib


def get_identity():
    identity_file = Path(__file__).parents[2] / "data" / "identity.toml"

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
