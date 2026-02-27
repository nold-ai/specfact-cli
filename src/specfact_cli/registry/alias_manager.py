"""Alias storage and resolution: alias -> command name."""

from __future__ import annotations

import json
from pathlib import Path

from beartype import beartype
from icontract import ensure, require

from specfact_cli.common import get_bridge_logger


logger = get_bridge_logger(__name__)

_ALIASES_FILENAME = "aliases.json"


def get_aliases_path() -> Path:
    """Return path to aliases.json under ~/.specfact/registry/."""
    return Path.home() / ".specfact" / "registry" / _ALIASES_FILENAME


def _builtin_command_names() -> set[str]:
    """Return set of built-in (default) command names for shadowing check."""
    from specfact_cli.registry.module_packages import CORE_MODULE_ORDER

    return set(CORE_MODULE_ORDER)


@beartype
@require(lambda alias: alias.strip() != "", "alias must be non-empty")
@require(lambda command_name: command_name.strip() != "", "command_name must be non-empty")
@ensure(lambda: True, "no postcondition on void")
def create_alias(alias: str, command_name: str, force: bool = False) -> None:
    """Store alias -> command_name in aliases.json. Warn or raise if alias shadows built-in."""
    alias = alias.strip()
    command_name = command_name.strip()
    path = get_aliases_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    builtin = _builtin_command_names()
    if alias in builtin and not force:
        logger.warning("Alias will shadow built-in module: %s", alias)
        raise ValueError(f'Alias "{alias}" would shadow built-in module. Use --force to proceed.')
    data = {}
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    data[alias] = command_name
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    if alias in builtin:
        logger.warning("Alias will shadow built-in module: %s", alias)


@beartype
@ensure(lambda result: isinstance(result, dict), "returns dict")
def list_aliases() -> dict[str, str]:
    """Return all alias -> command name mappings. Empty dict if file missing."""
    path = get_aliases_path()
    if not path.exists():
        return {}
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        return {}
    return {str(k): str(v) for k, v in data.items()}


@beartype
@require(lambda alias: alias.strip() != "", "alias must be non-empty")
@ensure(lambda: True, "no postcondition on void")
def remove_alias(alias: str) -> None:
    """Remove alias from aliases.json."""
    alias = alias.strip()
    path = get_aliases_path()
    if not path.exists():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    if alias in data:
        del data[alias]
        if data:
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        else:
            path.unlink()


@beartype
@require(lambda invoked_name: isinstance(invoked_name, str), "invoked_name must be str")
@ensure(lambda result: isinstance(result, str) and len(result) > 0, "returns non-empty string")
def resolve_command(invoked_name: str) -> str:
    """If invoked_name is an alias, return the stored command name; else return invoked_name."""
    aliases = list_aliases()
    if invoked_name in aliases:
        return aliases[invoked_name]
    return invoked_name
