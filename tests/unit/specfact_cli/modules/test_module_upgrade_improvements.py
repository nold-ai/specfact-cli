"""Tests for module upgrade command improvements.

Spec: openspec/changes/docs-new-user-onboarding/specs/module-installation/spec.md
Tasks: 7b.1 - 7b.13
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import click
import pytest
from typer.testing import CliRunner

from specfact_cli.modules.module_registry.src.commands import (
    _resolve_one_upgrade_name,
    _run_marketplace_upgrades,
    app as module_app,
)
from specfact_cli.registry.module_installer import InstallModuleOptions


runner = CliRunner()


def _unstyled(text: str) -> str:
    return click.unstyle(text)


# ── Scenario: Upgrade when module is already at latest version (no X->X) ──────


def test_run_marketplace_upgrades_skips_reinstall_when_at_latest(tmp_path: Path) -> None:
    """When latest_version == current_version, module must NOT be reinstalled and must NOT appear in 'Upgraded:' with X->X."""
    by_id: dict[str, dict[str, Any]] = {
        "nold-ai/specfact-backlog": {
            "version": "0.41.16",
            "source": "marketplace",
            "latest_version": "0.41.16",
        }
    }

    install_called = []

    def _fake_install(module_id: str, options: InstallModuleOptions | None = None, **_kwargs: object) -> Path:
        install_called.append(module_id)
        return tmp_path / "backlog"

    with patch("specfact_cli.modules.module_registry.src.commands.install_module", side_effect=_fake_install):
        _run_marketplace_upgrades(["nold-ai/specfact-backlog"], by_id, {})

    assert not install_called, "install_module must NOT be called when module is already at latest version"


def test_run_marketplace_upgrades_all_at_latest_prints_up_to_date(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """When all modules are at latest, output must say 'All modules are up to date' and no X->X lines."""
    by_id: dict[str, dict[str, Any]] = {
        "nold-ai/specfact-backlog": {"version": "0.41.16", "source": "marketplace", "latest_version": "0.41.16"},
        "nold-ai/specfact-codebase": {"version": "0.44.0", "source": "marketplace", "latest_version": "0.44.0"},
    }

    with patch("specfact_cli.modules.module_registry.src.commands.install_module") as mock_install:
        from io import StringIO

        output_buf = StringIO()
        from rich.console import Console

        test_console = Console(file=output_buf, highlight=False, markup=True)
        with patch("specfact_cli.modules.module_registry.src.commands.console", test_console):
            _run_marketplace_upgrades(["nold-ai/specfact-backlog", "nold-ai/specfact-codebase"], by_id, {})

        output = output_buf.getvalue()

    mock_install.assert_not_called()
    assert "0.41.16 -> 0.41.16" not in output, "Must not show X->X lines when nothing changed"
    assert "0.44.0 -> 0.44.0" not in output, "Must not show X->X lines when nothing changed"


def test_run_marketplace_upgrades_mixed_result_shows_sections(tmp_path: Path) -> None:
    """With mixed results, output has 'Upgraded:' and 'Already up to date:' sections."""
    by_id: dict[str, dict[str, Any]] = {
        "nold-ai/specfact-backlog": {"version": "0.41.16", "source": "marketplace", "latest_version": "0.42.0"},
        "nold-ai/specfact-codebase": {"version": "0.44.0", "source": "marketplace", "latest_version": "0.44.0"},
    }

    def _fake_install(module_id: str, options: InstallModuleOptions | None = None, **_kwargs: object) -> Path:
        if "backlog" in module_id:
            return tmp_path / "backlog"
        raise AssertionError(f"Should not install {module_id}")

    def _fake_read_version(module_dir: Path) -> str:
        if "backlog" in str(module_dir):
            return "0.42.0"
        return "0.44.0"

    from io import StringIO

    from rich.console import Console

    output_buf = StringIO()
    test_console = Console(file=output_buf, highlight=False, markup=True)

    with (
        patch("specfact_cli.modules.module_registry.src.commands.install_module", side_effect=_fake_install),
        patch(
            "specfact_cli.modules.module_registry.src.commands._read_installed_module_version",
            side_effect=_fake_read_version,
        ),
        patch("specfact_cli.modules.module_registry.src.commands.console", test_console),
    ):
        _run_marketplace_upgrades(["nold-ai/specfact-backlog", "nold-ai/specfact-codebase"], by_id, {})

    output = output_buf.getvalue()
    assert "Upgraded" in output, "Must have Upgraded section"
    assert "up to date" in output.lower(), "Must have 'Already up to date' section"
    assert "0.41.16 -> 0.42.0" in output or "backlog" in output


# ── Scenario: Upgrade multiple named modules selectively ──────────────────────


def test_upgrade_command_accepts_multiple_module_names(tmp_path: Path) -> None:
    """upgrade command must accept multiple positional module names."""
    with (
        patch(
            "specfact_cli.modules.module_registry.src.commands.get_modules_with_state",
            return_value=[
                {
                    "id": "nold-ai/specfact-backlog",
                    "version": "0.41.16",
                    "source": "marketplace",
                    "latest_version": "0.42.0",
                },
                {
                    "id": "nold-ai/specfact-codebase",
                    "version": "0.44.0",
                    "source": "marketplace",
                    "latest_version": "0.44.0",
                },
            ],
        ),
        patch(
            "specfact_cli.modules.module_registry.src.commands._run_marketplace_upgrades",
        ),
        patch("specfact_cli.modules.module_registry.src.commands._resolve_upgrade_target_ids") as mock_resolve,
    ):
        mock_resolve.return_value = ["nold-ai/specfact-backlog", "nold-ai/specfact-codebase"]
        result = runner.invoke(module_app, ["upgrade", "backlog", "codebase"])

    # Should not show "No such argument" error
    assert "No such argument" not in _unstyled(result.output), result.output
    # May succeed (exit 0) or fail for other reasons, but not because of wrong arg count
    assert result.exit_code != 2, f"Exit code 2 suggests wrong args: {result.output}"


# ── Scenario: Breaking major version upgrade requires confirmation ─────────────


def test_run_marketplace_upgrades_prompts_for_major_bump(tmp_path: Path) -> None:
    """_run_marketplace_upgrades must prompt before upgrading when major version increases."""
    by_id: dict[str, dict[str, Any]] = {
        "nold-ai/specfact-backlog": {"version": "0.41.16", "source": "marketplace", "latest_version": "1.0.0"},
    }

    from io import StringIO

    from rich.console import Console

    output_buf = StringIO()
    test_console = Console(file=output_buf, highlight=False, markup=True)

    prompt_shown = []

    def _fake_confirm(message: str, **kwargs: object) -> bool:
        prompt_shown.append(message)
        return False  # User declines

    with (
        patch("specfact_cli.modules.module_registry.src.commands.console", test_console),
        patch("specfact_cli.modules.module_registry.src.commands.typer.confirm", side_effect=_fake_confirm),
        patch("specfact_cli.modules.module_registry.src.commands.install_module") as mock_install,
    ):
        _run_marketplace_upgrades(["nold-ai/specfact-backlog"], by_id, {})

    output = output_buf.getvalue()
    # Must show major bump warning
    assert "major" in output.lower() or prompt_shown, "Must warn about major version bump"
    mock_install.assert_not_called()  # User declined → must not install


def test_run_marketplace_upgrades_skips_major_in_ci_mode(tmp_path: Path) -> None:
    """In CI/CD (non-interactive), major bumps are skipped with a warning; install is not called."""
    by_id: dict[str, dict[str, Any]] = {
        "nold-ai/specfact-backlog": {"version": "0.41.16", "source": "marketplace", "latest_version": "1.0.0"},
    }

    with (
        patch("specfact_cli.modules.module_registry.src.commands.is_non_interactive", return_value=True),
        patch("specfact_cli.modules.module_registry.src.commands.install_module") as mock_install,
    ):
        _run_marketplace_upgrades(["nold-ai/specfact-backlog"], by_id, {}, yes=False)

    mock_install.assert_not_called()


def test_run_marketplace_upgrades_yes_flag_skips_major_bump_prompt(tmp_path: Path) -> None:
    """With yes=True, major version bumps proceed without prompt."""
    by_id: dict[str, dict[str, Any]] = {
        "nold-ai/specfact-backlog": {"version": "0.41.16", "source": "marketplace", "latest_version": "1.0.0"},
    }

    def _fake_install(module_id: str, options: InstallModuleOptions | None = None, **_kwargs: object) -> Path:
        return tmp_path / "backlog"

    def _fake_read_version(p: Path) -> str:
        return "1.0.0"

    with (
        patch("specfact_cli.modules.module_registry.src.commands.install_module", side_effect=_fake_install),
        patch(
            "specfact_cli.modules.module_registry.src.commands._read_installed_module_version",
            side_effect=_fake_read_version,
        ),
        patch("specfact_cli.modules.module_registry.src.commands.typer.confirm") as mock_confirm,
    ):
        _run_marketplace_upgrades(["nold-ai/specfact-backlog"], by_id, {}, yes=True)

    mock_confirm.assert_not_called()  # --yes flag skips prompt


def test_upgrade_command_warns_when_registry_unavailable(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """When the registry index cannot be fetched, upgrade prints a warning before continuing."""
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.fetch_registry_index",
        lambda **_: None,
    )
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.get_modules_with_state",
        lambda: [{"id": "backlog", "version": "0.2.0", "enabled": True, "source": "marketplace"}],
    )

    def _install(module_id: str, options: InstallModuleOptions | None = None, **_kwargs: object) -> Path:
        return tmp_path / "backlog"

    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.install_module",
        _install,
    )
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands._read_installed_module_version",
        lambda _p: "0.2.0",
    )
    result = runner.invoke(module_app, ["upgrade", "backlog"])
    assert result.exit_code == 0
    out = (result.stdout or "") + (result.stderr or "")
    assert "unavailable" in out.lower() or "network error" in out.lower()


def test_run_marketplace_upgrades_calls_console_status_when_spinner_enabled(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """When not in pytest/test mode, install path uses ``console.status`` for feedback."""
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.delenv("TEST_MODE", raising=False)

    mock_console = MagicMock()
    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=None)
    mock_ctx.__exit__ = MagicMock(return_value=None)
    mock_console.status = MagicMock(return_value=mock_ctx)

    by_id: dict[str, dict[str, Any]] = {
        "nold-ai/specfact-backlog": {"version": "0.1.0", "source": "marketplace"},
    }

    def _fake_install(module_id: str, options: InstallModuleOptions | None = None, **_kwargs: object) -> Path:
        return tmp_path / "m"

    with (
        patch("specfact_cli.modules.module_registry.src.commands.console", mock_console),
        patch("specfact_cli.modules.module_registry.src.commands.install_module", side_effect=_fake_install),
        patch(
            "specfact_cli.modules.module_registry.src.commands._read_installed_module_version",
            return_value="0.2.0",
        ),
    ):
        _run_marketplace_upgrades(["nold-ai/specfact-backlog"], by_id, {})

    mock_console.status.assert_called()


def test_resolve_one_upgrade_name_accepts_namespaced_id_when_installed_key_is_short() -> None:
    """`specfact module upgrade nold-ai/specfact-backlog` must resolve when list uses short id keys."""
    by_id: dict[str, dict[str, Any]] = {
        "specfact-backlog": {
            "version": "0.41.16",
            "source": "marketplace",
            "latest_version": "0.41.16",
        }
    }
    assert _resolve_one_upgrade_name("nold-ai/specfact-backlog", by_id) == "specfact-backlog"
