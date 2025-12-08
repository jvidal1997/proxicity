"""
Module for hot-reloading all project modules during development.

Provides a utility function `reload_everything()` that reloads all Python modules
under the project package (defined by `PROJECT_ROOT`) in top-down order, ensuring
parent packages are reloaded before submodules. Useful for iterative development
and testing without restarting the Python interpreter.
"""
import importlib
import sys
from types import ModuleType

# Adjust this to match your project root package name
PROJECT_ROOT = "proxicity"


def reload_everything():
    """
    Reload all modules under the project package, including Settings,
    in correct top-down order. Safe for development hot-reloads.
    """
    modules_to_reload = []

    # Collect module objects that belong to your project
    for name, module in sys.modules.items():
        if isinstance(module, ModuleType) and name.startswith(PROJECT_ROOT):
            modules_to_reload.append((name, module))

    # Sort so parent packages reload before submodules
    modules_to_reload.sort(key=lambda pair: pair[0].count("."))

    print("\nReloading project modules...\n")

    for name, module in modules_to_reload:
        try:
            importlib.reload(module)
            print(f"Reloaded {name}")
        except Exception as e:
            print(f"FAILED to reload {name}: {e}")

    print("\nReload complete.\n")