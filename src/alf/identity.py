"""
ALF identity management.
"""

import tomllib
from importlib.metadata import version as package_version

from .capabilities import discover_capabilities
from .paths import get_data_directory


def get_identity():
    identity_file = get_data_directory() / "identity.toml"

    with open(identity_file, "rb") as file:
        identity = tomllib.load(file)

    identity["version"] = package_version("alf")

    return identity


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
