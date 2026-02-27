"""Unit tests for alias manager (create, list, remove, resolve with shadow warning)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from specfact_cli.registry.alias_manager import (
    create_alias,
    get_aliases_path,
    list_aliases,
    remove_alias,
    resolve_command,
)


def test_get_aliases_path_returns_specfact_registry_path() -> None:
    """get_aliases_path() returns path under ~/.specfact/registry/aliases.json."""
    path = get_aliases_path()
    assert path.name == "aliases.json"
    assert ".specfact" in path.parts
    assert "registry" in path.parts


def test_create_alias_stores_mapping(tmp_path: Path) -> None:
    """create_alias() writes alias -> command name to aliases.json."""
    with patch("specfact_cli.registry.alias_manager.get_aliases_path", return_value=tmp_path / "aliases.json"):
        create_alias("my-backlog", "backlog-pro")
    assert (tmp_path / "aliases.json").exists()
    data = json.loads((tmp_path / "aliases.json").read_text())
    assert data == {"my-backlog": "backlog-pro"}


def test_list_aliases_returns_all_aliases(tmp_path: Path) -> None:
    """list_aliases() returns dict of alias -> command name."""
    aliases_file = tmp_path / "aliases.json"
    tmp_path.mkdir(parents=True, exist_ok=True)
    aliases_file.write_text(json.dumps({"backlog": "backlog-pro", "generate": "generate"}))
    with patch("specfact_cli.registry.alias_manager.get_aliases_path", return_value=aliases_file):
        result = list_aliases()
    assert result == {"backlog": "backlog-pro", "generate": "generate"}


def test_list_aliases_returns_empty_when_file_missing() -> None:
    """list_aliases() returns empty dict when aliases file does not exist."""
    with patch("specfact_cli.registry.alias_manager.get_aliases_path") as mock_path:
        mock_path.return_value = Path("/nonexistent/specfact/registry/aliases.json")
        result = list_aliases()
    assert result == {}


def test_remove_alias_deletes_mapping(tmp_path: Path) -> None:
    """remove_alias() removes alias from aliases.json."""
    aliases_file = tmp_path / "aliases.json"
    tmp_path.mkdir(parents=True, exist_ok=True)
    aliases_file.write_text(json.dumps({"backlog": "acme/backlog-pro", "other": "ns/other"}))
    with patch("specfact_cli.registry.alias_manager.get_aliases_path", return_value=aliases_file):
        remove_alias("backlog")
    data = json.loads(aliases_file.read_text())
    assert data == {"other": "ns/other"}


def test_resolve_command_returns_module_command_name_when_aliased() -> None:
    """resolve_command() returns the stored command name for the alias."""
    with patch("specfact_cli.registry.alias_manager.list_aliases", return_value={"backlog": "backlog-pro"}):
        assert resolve_command("backlog") == "backlog-pro"
    with patch("specfact_cli.registry.alias_manager.list_aliases", return_value={"gen": "generate"}):
        assert resolve_command("gen") == "generate"


def test_resolve_command_returns_invoked_name_when_not_aliased() -> None:
    """resolve_command() returns the same name when no alias exists."""
    with patch("specfact_cli.registry.alias_manager.list_aliases", return_value={}):
        assert resolve_command("backlog") == "backlog"
    with patch("specfact_cli.registry.alias_manager.list_aliases", return_value={"other": "x/y"}):
        assert resolve_command("backlog") == "backlog"


def test_create_alias_raises_when_shadowing_builtin_without_force(tmp_path: Path) -> None:
    """When alias shadows built-in and force=False, create_alias raises ValueError."""
    with (
        patch("specfact_cli.registry.alias_manager.get_aliases_path", return_value=tmp_path / "aliases.json"),
        patch("specfact_cli.registry.alias_manager._builtin_command_names", return_value={"backlog", "module"}),
        pytest.raises(ValueError, match="shadow"),
    ):
        create_alias("backlog", "backlog-pro", force=False)


def test_create_alias_with_force_stores_even_when_shadowing(tmp_path: Path) -> None:
    """When alias shadows built-in and force=True, create_alias stores the mapping."""
    with (
        patch("specfact_cli.registry.alias_manager.get_aliases_path", return_value=tmp_path / "aliases.json"),
        patch("specfact_cli.registry.alias_manager._builtin_command_names", return_value={"backlog"}),
    ):
        create_alias("backlog", "backlog-pro", force=True)
    data = json.loads((tmp_path / "aliases.json").read_text())
    assert data.get("backlog") == "backlog-pro"
