"""
ALF introspection and health checks.

Provides information about ALF's internal structure and state.
"""

import importlib
import pkgutil

import alf


def check_modules():
    """
    Report ALF modules and their capability status.
    """

    advertising_modules = []
    non_reporting_modules = []
    failed_modules = []

    for module_info in pkgutil.iter_modules(alf.__path__):
        module_name = f"alf.{module_info.name}"

        try:
            module = importlib.import_module(module_name)

        except Exception as exc:
            failed_modules.append(
                {
                    "module": module_name,
                    "error": str(exc),
                }
            )
            continue

        if hasattr(module, "get_capability"):
            advertising_modules.append(module_name)
        else:
            non_reporting_modules.append(module_name)

    return {
        "name": "Modules",
        "healthy": len(failed_modules) == 0,
        "details": {
            "advertising_modules": advertising_modules,
            "non_reporting_modules": non_reporting_modules,
            "failed_modules": failed_modules,
        },
    }


def get_health_report():
    """
    Run all health checks.
    """

    checks = [
        check_modules(),
    ]

    return {
        "healthy": all(check["healthy"] for check in checks),
        "checks": checks,
    }
