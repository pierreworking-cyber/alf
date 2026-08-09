"""
ALF introspection and health checks.

Provides information about ALF's internal structure and state.
"""

import importlib
import pkgutil

import alf

REQUIRED_COMMAND_FIELDS = [
    "id",
    "help",
    "usage",
]

def discover_modules():
    """
    Discover and import ALF modules.
    """

    modules = []

    for module_info in pkgutil.iter_modules(alf.__path__):
        module_name = f"alf.{module_info.name}"

        try:
            module = importlib.import_module(module_name)

        except Exception as exc:
            modules.append(
                {
                    "name": module_name,
                    "module": None,
                    "error": str(exc),
                }
            )
            continue

        modules.append(
            {
                "name": module_name,
                "module": module,
                "error": None,
            }
        )

    return modules


def check_modules(modules):
    """
    Report ALF modules and their capability status.
    """

    advertising_modules = []
    non_reporting_modules = []
    failed_modules = []

    for discovered in modules:
        module_name = discovered["name"]
        module = discovered["module"]

        if module is None:
            failed_modules.append(
                {
                    "module": module_name,
                    "error": discovered["error"],
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


def check_command_integrity(modules):
    """
    Check the command catalogue and handlers for consistency.
    """

    warnings = []
    command_ids = set()

    commands_module = next(
        (
            discovered["module"]
            for discovered in modules
            if discovered["name"] == "alf.commands"
        ),
        None,
    )

    if commands_module is None:
        return {
            "name": "Commands",
            "healthy": False,
            "details": {
                "warnings": [
                    {
                        "message": "Commands module could not be loaded",
                    }
                ],
            },
        }

    catalogue = commands_module.commands
    handlers = commands_module.command_handlers
    required_fields = REQUIRED_COMMAND_FIELDS

    for name, command in catalogue.items():
        for field in required_fields:
            if field not in command:
                warnings.append(
                    {
                        "command": name,
                        "message": f"Command has no {field}",
                    }
                )

        if name not in handlers:
            warnings.append(
                {
                    "command": name,
                    "message": "Command has no handler",
                }
            )

        command_id = command.get("id")

        if not command_id:
            warnings.append(
                {
                    "command": name,
                    "message": "Command has no id",
                }
            )
            continue

        if command_id in command_ids:
            warnings.append(
                {
                    "command": name,
                    "message": f"Duplicate command id: {command_id}",
                }
            )
            continue

        command_ids.add(command_id)

    for name in handlers:
        if name not in catalogue:
            warnings.append(
                {
                    "command": name,
                    "message": "Handler has no catalogue entry",
                }
            )

    return {
        "name": "Commands",
        "healthy": len(warnings) == 0,
        "details": {
            "warnings": warnings,
        },
    }


def get_health_report():
    """
    Run all health checks.
    """

    modules = discover_modules()

    checks = [
        check_modules(modules),
        check_command_integrity(modules),
    ]

    return {
        "healthy": all(check["healthy"] for check in checks),
        "checks": checks,
    }
