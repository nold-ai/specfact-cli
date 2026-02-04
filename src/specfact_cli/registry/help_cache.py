"""
Help cache: persist command metadata under ~/.specfact/registry for fast root help.

Discovery runs on specfact init; root --help can render from cache without loading command modules.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from beartype import beartype


def get_registry_dir() -> Path:
    """Return registry directory (~/.specfact/registry). Uses SPECFACT_REGISTRY_DIR if set (e.g. tests)."""
    env_dir = __registry_dir_override()
    if env_dir is not None:
        return Path(env_dir)
    return Path.home() / ".specfact" / "registry"


def __registry_dir_override() -> str | None:
    """Return override directory from env (for tests); None to use default."""
    import os

    return os.environ.get("SPECFACT_REGISTRY_DIR")


def get_commands_cache_path() -> Path:
    """Return path to commands cache file (commands.json)."""
    return get_registry_dir() / "commands.json"


@beartype
def write_commands_cache(
    commands: list[tuple[str, str, str]],
    version: str,
) -> None:
    """
    Write command metadata to ~/.specfact/registry/commands.json.

    Args:
        commands: List of (name, help, tier).
        version: SpecFact version for cache invalidation.
    """
    registry_dir = get_registry_dir()
    registry_dir.mkdir(parents=True, exist_ok=True)
    path = get_commands_cache_path()
    data: dict[str, Any] = {
        "version": version,
        "commands": [{"name": n, "help": h, "tier": t} for n, h, t in commands],
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


@beartype
def read_commands_cache() -> tuple[list[tuple[str, str, str]], str] | None:
    """
    Read commands cache if present and well-formed.

    Returns:
        ((name, help, tier), version) or None if missing/invalid.
    """
    path = get_commands_cache_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict) or "version" not in data or "commands" not in data:
        return None
    version = str(data["version"])
    raw = data.get("commands")
    if not isinstance(raw, list):
        return None
    out: list[tuple[str, str, str]] = []
    for item in raw:
        if isinstance(item, dict) and "name" in item and "help" in item:
            out.append((str(item["name"]), str(item.get("help", "")), str(item.get("tier", "community"))))
        else:
            return None
    return (out, version)


@beartype
def is_cache_valid(current_version: str) -> bool:
    """Return True if cache exists and its version matches current_version."""
    parsed = read_commands_cache()
    if parsed is None:
        return False
    _commands, cache_version = parsed
    return cache_version == current_version


def print_root_help_from_cache() -> None:
    """
    Print root help (Usage + Commands) from cache and exit.

    Use when cache is valid and argv is root --help. Does not load command modules.
    """
    from rich.console import Console
    from rich.table import Table

    parsed = read_commands_cache()
    if parsed is None:
        return
    commands, _ = parsed
    console = Console()
    console.print("Usage: specfact [OPTIONS] COMMAND [ARGS]...")
    console.print()
    console.print("  SpecFact CLI - Spec → Contract → Sentinel for Contract-Driven Development")
    console.print()
    console.print("Options:")
    console.print("  --version, -v       Show version and exit")
    console.print("  --banner            Show ASCII art banner")
    console.print("  --mode [cicd|copilot]  Operational mode")
    console.print("  --debug             Enable debug output")
    console.print("  --help, -h          Show this message and exit")
    console.print()
    table = Table(show_header=True, header_style="bold")
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="dim")
    for name, help_str, _ in commands:
        table.add_row(name, help_str)
    console.print("Commands:")
    console.print(table)


def run_discovery_and_write_cache(version: str) -> None:
    """
    Run discovery from CommandRegistry and write commands.json.

    Call from specfact init after existing logic. Does not invoke command loaders.
    """
    from specfact_cli.registry.registry import CommandRegistry

    commands = [(meta.name, meta.help, meta.tier) for _name, meta in CommandRegistry.list_commands_for_help()]
    write_commands_cache(commands, version)
