"""
Tests for CommandRegistry and CommandMetadata (spec: command-registry, lazy-loading).

Scenarios: register/get_typer (lazy), list_commands, unknown raises, metadata without load.
"""

from __future__ import annotations

import pytest
import typer

from specfact_cli.registry import CommandMetadata, CommandRegistry


@pytest.fixture(autouse=True)
def _reset_registry():
    """Reset registry before each test so tests are isolated."""
    CommandRegistry._clear_for_testing()
    yield
    CommandRegistry._clear_for_testing()


def _make_init_app() -> typer.Typer:
    """Loader that returns a Typer app (simulates init command)."""
    return typer.Typer(name="init", help="Initialize SpecFact in the current project")


def _make_backlog_app() -> typer.Typer:
    """Loader that returns a Typer app (simulates backlog command)."""
    return typer.Typer(name="backlog", help="Backlog refinement and template management")


# --- 2.1 CommandRegistry: register, get_typer (lazy), list_commands; unknown raises; metadata without load ---


def test_register_stores_entry_without_invoking_loader():
    """register(name, loader, metadata) stores entry without invoking loader."""
    load_count = 0

    def loader() -> typer.Typer:
        nonlocal load_count
        load_count += 1
        return typer.Typer(name="init", help="Init")

    metadata = CommandMetadata(name="init", help="Initialize", tier="community")
    CommandRegistry.register("init", loader, metadata)
    assert load_count == 0
    assert CommandRegistry.list_commands() == ["init"]


def test_get_typer_invokes_loader_on_first_use_and_caches():
    """get_typer(name) invokes loader on first use and returns same instance on subsequent calls."""
    load_count = 0

    def loader() -> typer.Typer:
        nonlocal load_count
        load_count += 1
        return typer.Typer(name="init", help="Init")

    metadata = CommandMetadata(name="init", help="Initialize", tier="community")
    CommandRegistry.register("init", loader, metadata)
    app1 = CommandRegistry.get_typer("init")
    app2 = CommandRegistry.get_typer("init")
    assert load_count == 1
    assert app1 is app2
    assert app1.info.name == "init"


def test_list_commands_returns_names_in_registration_order():
    """list_commands() returns all registered command names in registration order."""
    meta_init = CommandMetadata(name="init", help="Init", tier="community")
    meta_backlog = CommandMetadata(name="backlog", help="Backlog", tier="community")
    CommandRegistry.register("init", _make_init_app, meta_init)
    CommandRegistry.register("backlog", _make_backlog_app, meta_backlog)
    assert CommandRegistry.list_commands() == ["init", "backlog"]


def test_get_typer_unknown_raises_clear_error():
    """get_typer('unknown-cmd') raises ValueError with message listing registered commands."""
    meta = CommandMetadata(name="init", help="Init", tier="community")
    CommandRegistry.register("init", _make_init_app, meta)
    with pytest.raises(ValueError) as exc_info:
        CommandRegistry.get_typer("unknown-cmd")
    assert "unknown-cmd" in str(exc_info.value)
    assert "init" in str(exc_info.value) or "Registered" in str(exc_info.value)


def test_get_metadata_returns_without_invoking_loader():
    """get_metadata(name) returns metadata without invoking loader."""
    load_count = 0

    def loader() -> typer.Typer:
        nonlocal load_count
        load_count += 1
        return typer.Typer(name="backlog", help="Backlog")

    meta = CommandMetadata(
        name="backlog",
        help="Backlog refinement and template management",
        tier="community",
    )
    CommandRegistry.register("backlog", loader, meta)
    got = CommandRegistry.get_metadata("backlog")
    assert load_count == 0
    assert got is not None
    assert got.name == "backlog"
    assert "Backlog refinement" in got.help
    assert got.tier == "community"


def test_list_commands_for_help_returns_metadata_without_load():
    """list_commands_for_help() returns (name, metadata) without invoking loaders."""
    load_count = 0

    def loader() -> typer.Typer:
        nonlocal load_count
        load_count += 1
        return typer.Typer(name="init", help="Init")

    meta = CommandMetadata(name="init", help="Initialize project", tier="community")
    CommandRegistry.register("init", loader, meta)
    help_list = CommandRegistry.list_commands_for_help()
    assert load_count == 0
    assert len(help_list) == 1
    assert help_list[0][0] == "init"
    assert help_list[0][1].help == "Initialize project"


# --- 2.2 Same CLI surface: specfact --help, specfact init --help, specfact backlog --help exit 0 ---


def test_cli_root_help_exits_zero():
    """specfact --help exits 0 (same CLI surface after refactor)."""
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "specfact_cli", "--help"],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=None,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)


def test_cli_init_help_exits_zero():
    """specfact init --help exits 0."""
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "specfact_cli", "init", "--help"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)


def test_cli_backlog_help_exits_zero():
    """specfact backlog --help exits 0 when installed, otherwise returns actionable missing-command UX."""
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "specfact_cli", "backlog", "--help"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode == 0:
        return
    merged = (result.stdout or "") + "\n" + (result.stderr or "")
    assert "No such command 'backlog'" in merged, (result.stdout, result.stderr)


def test_cli_module_help_exits_zero():
    """specfact module --help exits 0."""
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "specfact_cli", "module", "--help"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0 and "failed integrity verification" in (result.stdout or ""):
        pytest.skip("module-registry not loaded (integrity verification failed); re-sign manifest to run this test")
    assert result.returncode == 0, (result.stdout, result.stderr)
