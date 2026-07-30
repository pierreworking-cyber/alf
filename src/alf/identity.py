"""
ALF identity management.
"""

from pathlib import Path
import tomllib


def get_identity():
    identity_file = Path(__file__).parents[2] / "data" / "identity.toml"

    with open(identity_file, "rb") as file:
        return tomllib.load(file)
