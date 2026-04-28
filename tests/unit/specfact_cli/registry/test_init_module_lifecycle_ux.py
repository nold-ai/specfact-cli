"""Tests for `specfact init` bootstrap UX and `init ide` parity."""

from __future__ import annotations

from pathlib import Path

import click
from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.modules.init.src import commands as init_commands
from specfact_cli.utils.env_manager import EnvManager, EnvManagerInfo


runner = CliRunner()


def _unstyled(text: str) -> str:
    """Return console output with ANSI styling removed."""
    return click.unstyle(text)


def test_init_rejects_deprecated_list_modules_option(tmp_path: Path) -> None:
    """`specfact init --list-modules` is removed; lifecycle lives under `specfact module`."""

    result = runner.invoke(app, ["init", "--repo", str(tmp_path), "--list-modules"])
    output = _unstyled(result.output)

    assert result.exit_code != 0
    assert "No such option" in output
    assert "--list-modules" in output


def test_init_rejects_deprecated_enable_module_option(tmp_path: Path) -> None:
    """`specfact init --enable-module` is removed; use `specfact module enable`."""

    result = runner.invoke(app, ["init", "--repo", str(tmp_path), "--enable-module", "sync"])
    output = _unstyled(result.output)

    assert result.exit_code != 0
    assert "No such option" in output
    assert "--enable-module" in output


def test_init_rejects_deprecated_disable_module_option(tmp_path: Path) -> None:
    """`specfact init --disable-module` is removed; use `specfact module disable`."""

    result = runner.invoke(app, ["init", "--repo", str(tmp_path), "--disable-module", "sync"])
    output = _unstyled(result.output)

    assert result.exit_code != 0
    assert "No such option" in output
    assert "--disable-module" in output


def test_init_bootstrap_only_does_not_run_ide_setup(tmp_path: Path, monkeypatch) -> None:
    """Top-level init should not run template copy; it should stay bootstrap-only."""

    monkeypatch.setattr("specfact_cli.modules.init.src.commands.is_first_run", lambda **_kwargs: False)
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.get_discovered_modules_for_state",
        lambda enable_ids=None, disable_ids=None, base_path=None, preserve_existing=False: [
            {"id": "sync", "version": "0.1.0", "enabled": True},
        ],
    )
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.write_modules_state", lambda modules: None)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.run_discovery_and_write_cache", lambda version: None)

    def _fail_copy(*args, **kwargs):
        raise AssertionError("copy_templates_to_ide must not be called by top-level init")

    monkeypatch.setattr("specfact_cli.modules.init.src.commands.copy_templates_to_ide", _fail_copy)

    result = runner.invoke(app, ["init", "--repo", str(tmp_path)])
    assert result.exit_code == 0
    assert "Use `specfact init ide`" in result.stdout
    assert "module management has moved" in result.stdout.lower()


def test_init_install_deps_runs_without_ide_template_copy(tmp_path: Path, monkeypatch) -> None:
    """Top-level init --install-deps installs dependencies without invoking IDE template copy."""

    monkeypatch.setattr("specfact_cli.modules.init.src.commands.is_first_run", lambda **_kwargs: False)
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.get_discovered_modules_for_state",
        lambda enable_ids=None, disable_ids=None, base_path=None, preserve_existing=False: [
            {"id": "sync", "version": "0.1.0", "enabled": True},
        ],
    )
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.write_modules_state", lambda modules: None)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.run_discovery_and_write_cache", lambda version: None)
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.detect_env_manager",
        lambda repo_path: EnvManagerInfo(
            manager=EnvManager.PIP,
            available=True,
            command_prefix=[],
            message="pip",
        ),
    )

    calls: list[list[str]] = []

    class _Result:
        returncode = 0

    def _fake_run(cmd, capture_output, text, check, cwd, timeout):
        calls.append(list(cmd))
        return _Result()

    monkeypatch.setattr("specfact_cli.modules.init.src.commands.subprocess.run", _fake_run)

    def _fail_copy(*args, **kwargs):
        raise AssertionError("copy_templates_to_ide must not be called by top-level init --install-deps")

    monkeypatch.setattr("specfact_cli.modules.init.src.commands.copy_templates_to_ide", _fail_copy)

    result = runner.invoke(app, ["init", "--repo", str(tmp_path), "--install-deps"])

    assert result.exit_code == 0
    assert calls, "Expected dependency installation command to run"
    assert calls[0][:4] == ["pip", "install", "-U", "beartype>=0.22.4"]


def test_resolve_templates_dir_none_when_no_discoverable_prompts(tmp_path: Path, monkeypatch) -> None:
    """Workflow prompts ship in bundles; without modules or dev repo prompts, resolution is None."""
    monkeypatch.setattr(
        init_commands,
        "discover_prompt_template_files",
        lambda repo_path, include_package_fallback=True: [],
    )

    resolved = init_commands._resolve_templates_dir(tmp_path)

    assert resolved is None
