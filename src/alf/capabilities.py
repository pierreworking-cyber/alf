"""
ALF capability discovery.

Discovers modules that advertise capabilities.
"""

import importlib
import pkgutil

import alf


def get_provider_modules():
    """
    Find ALF modules that may provide capabilities.
    """

    providers = []

    for module_info in pkgutil.iter_modules(alf.__path__):
        module_name = f"alf.{module_info.name}"

        module = importlib.import_module(module_name)

        if hasattr(module, "get_capability"):
            providers.append(module)

    return providers


def get_capabilities():
    """
    Collect capabilities from providers.
    """

    capabilities = []

    for provider in get_provider_modules():
        capabilities.append(
            provider.get_capability()
        )

    return capabilities
