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
        capabilities.append(provider.get_capability())

    return capabilities


def discover_capabilities():
    """
    Discover capabilities and validate capability contracts.
    """
    capabilities = []
    warnings = []
    capability_ids = set()

    for provider in get_provider_modules():
        try:
            capability = provider.get_capability()

            capability_id = capability.get("id")

            if not capability_id:
                warnings.append(
                    {
                        "module": provider.__name__,
                        "message": "Capability has no id",
                    }
                )
                continue

            if capability_id in capability_ids:
                warnings.append(
                    {
                        "module": provider.__name__,
                        "message": f"Duplicate capability id: {capability_id}",
                    }
                )
                continue

            capability_ids.add(capability_id)
            capabilities.append(capability)

        except Exception as exc:
            warnings.append(
                {
                    "module": provider.__name__,
                    "message": str(exc),
                }
            )

    return {
        "capabilities": capabilities,
        "warnings": warnings,
    }
