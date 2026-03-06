"""
Tests for help cache (spec: help-cache).

Scenarios: init writes commands.json; root help uses cache when valid; cache invalidation.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from specfact_cli.registry import CommandMetadata, CommandRegistry
from specfact_cli.registry.help_cache import (
    get_commands_cache_path,
    get_registry_dir,
    is_cache_valid,
    read_commands_cache,
    run_discovery_and_write_cache,
    write_commands_cache,
)


REPO_ROOT = Path(__file__).resolve().parents[4]
SRC_ROOT = REPO_ROOT / "src"


def _subprocess_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    pythonpath_parts = [str(SRC_ROOT), str(REPO_ROOT)]
    if existing:
        pythonpath_parts.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
    if extra:
        env.update(extra)
    return env


@pytest.fixture
def registry_dir(tmp_path: Path):
    """Use tmp_path as registry dir for tests."""
    os.environ["SPECFACT_REGISTRY_DIR"] = str(tmp_path)
    try:
        yield tmp_path
    finally:
        os.environ.pop("SPECFACT_REGISTRY_DIR", None)


@pytest.fixture(autouse=True)
def _reset_registry():
    """Reset registry before each test."""
    CommandRegistry._clear_for_testing()
    yield
    CommandRegistry._clear_for_testing()


def test_get_registry_dir_uses_override(registry_dir: Path):
    """SPECFACT_REGISTRY_DIR is used when set."""
    assert get_registry_dir() == registry_dir


def test_write_commands_cache_creates_dir_and_file(registry_dir: Path):
    """write_commands_cache creates ~/.specfact/registry/ and commands.json."""
    commands = [("init", "Initialize", "community"), ("backlog", "Backlog stuff", "community")]
    write_commands_cache(commands, "0.27.0")
    path = get_commands_cache_path()
    assert path.exists()
    assert path.read_text()
    data = path.read_text()
    assert "0.27.0" in data
    assert "init" in data
    assert "Initialize" in data


def test_read_commands_cache_returns_data_when_valid(registry_dir: Path):
    """read_commands_cache returns (commands, version) when file is valid."""
    commands = [("a", "Help A", "community"), ("b", "Help B", "community")]
    write_commands_cache(commands, "1.0.0")
    out = read_commands_cache()
    assert out is not None
    cmds, ver = out
    assert ver == "1.0.0"
    assert cmds == commands


def test_read_commands_cache_returns_none_when_missing(registry_dir: Path):
    """read_commands_cache returns None when file does not exist."""
    assert read_commands_cache() is None


def test_read_commands_cache_returns_none_when_invalid_json(registry_dir: Path):
    """read_commands_cache returns None when file is not valid JSON."""
    path = get_commands_cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("not json")
    assert read_commands_cache() is None


def test_is_cache_valid_true_when_version_matches(registry_dir: Path):
    """is_cache_valid returns True when cache version matches current."""
    write_commands_cache([("init", "Init", "community")], "0.27.0")
    assert is_cache_valid("0.27.0") is True


def test_is_cache_valid_false_when_version_differs(registry_dir: Path):
    """is_cache_valid returns False when cache version differs."""
    write_commands_cache([("init", "Init", "community")], "0.26.0")
    assert is_cache_valid("0.27.0") is False


def test_run_discovery_and_write_cache_writes_from_registry(registry_dir: Path):
    """run_discovery_and_write_cache writes commands from CommandRegistry without invoking loaders."""
    load_count = 0

    def loader():
        nonlocal load_count
        load_count += 1
        import typer

        return typer.Typer(name="init", help="Init")

    meta = CommandMetadata(name="init", help="Initialize project", tier="community")
    CommandRegistry.register("init", loader, meta)
    run_discovery_and_write_cache("0.27.0")
    assert load_count == 0
    out = read_commands_cache()
    assert out is not None
    cmds, ver = out
    assert ver == "0.27.0"
    assert len(cmds) == 1
    assert cmds[0][0] == "init"
    assert "Initialize" in cmds[0][1]


def test_cli_root_help_uses_cache_when_valid(registry_dir: Path):
    """When cache exists and is valid, specfact --help exits 0 and shows commands from cache."""
    from specfact_cli import __version__

    write_commands_cache(
        [("init", "Initialize SpecFact", "community"), ("backlog", "Backlog refinement", "community")],
        __version__,
    )
    result = subprocess.run(
        [sys.executable, "-m", "specfact_cli", "--help"],
        capture_output=True,
        text=True,
        timeout=30,
        env=_subprocess_env({"SPECFACT_REGISTRY_DIR": str(registry_dir)}),
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert "init" in result.stdout or "Initialize" in result.stdout.lower()
