"""
ALF introspection and health checks.

Provides information about ALF's internal structure and state.
"""

from .capabilities import get_alf_modules, get_provider_modules


def get_module_introspection():
    """
    Report ALF module capability participation.
    """

    all_modules = {
        module.__name__
        for module in get_alf_modules()
    }

    providers = {
        module.__name__
        for module in get_provider_modules()
    }

    return {
        "advertising_modules": sorted(providers),
        "non_reporting_modules": sorted(all_modules - providers),
    }


def get_health_report():
    """
    Return ALF introspection information.
    """

    return {
        "modules": get_module_introspection(),
    }
