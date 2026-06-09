"""Validate that a player file can be imported and instantiated without crashing.

Usage:
    uv run python -m game.validate players/fred.py

Exits 0 on success, 1 on any failure.
"""

import importlib.util
import sys
from pathlib import Path


def validate(player_file: str) -> None:
    path = Path(player_file)
    if not path.exists():
        print(f"ERROR: File not found: {player_file}")
        sys.exit(1)

    module_name = path.stem

    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        print(f"ERROR: Could not create module spec for {player_file}")
        sys.exit(1)

    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        print(f"ERROR: Player file crashed on import: {type(exc).__name__}: {exc}")
        sys.exit(1)

    player_class = next(
        (
            getattr(module, name)
            for name in dir(module)
            if name.lower() == module_name.lower() and isinstance(getattr(module, name), type)
        ),
        None,
    )

    if player_class is None:
        print(f"ERROR: No class named '{module_name}' (case-insensitive) found in {player_file}")
        sys.exit(1)

    try:
        instance = player_class()
    except Exception as exc:
        print(f"ERROR: Player class crashed during instantiation: {type(exc).__name__}: {exc}")
        sys.exit(1)

    if not callable(getattr(instance, "algo", None)):
        print("ERROR: Player class does not define an 'algo' method")
        sys.exit(1)

    print(f"OK: {module_name} imported and instantiated successfully")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m game.validate <player_file>")
        sys.exit(1)
    validate(sys.argv[1])
