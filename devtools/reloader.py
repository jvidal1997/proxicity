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

    print("\n🔄 Reloading project modules...\n")

    for name, module in modules_to_reload:
        try:
            importlib.reload(module)
            print(f"  ✔ reloaded {name}")
        except Exception as e:
            print(f"  ❌ FAILED to reload {name}: {e}")

    print("\n✨ Reload complete.\n")