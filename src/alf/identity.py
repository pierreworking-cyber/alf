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
