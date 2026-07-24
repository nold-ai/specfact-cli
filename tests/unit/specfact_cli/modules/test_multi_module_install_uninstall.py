"""Tests for multi-module install and uninstall.

Spec: openspec/changes/docs-new-user-onboarding/specs/module-installation/spec.md
Tasks: 7c.1 - 7c.9
"""

from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import patch

import click
import pytest
from typer.testing import CliRunner

from specfact_cli.cli import app, rebuild_root_app_from_registry
from specfact_cli.registry import CommandRegistry
from specfact_cli.registry.bootstrap import register_builtin_commands


@pytest.fixture(autouse=True)
def reset_registry_and_root_app() -> Generator[None, None, None]:
    """Other tests clear ``CommandRegistry`` without re-registering; rebuild root ``app`` for Typer."""
    CommandRegistry._clear_for_testing()
    register_builtin_commands()
    rebuild_root_app_from_registry()
    yield
    CommandRegistry._clear_for_testing()
    register_builtin_commands()
    rebuild_root_app_from_registry()


runner = CliRunner()


@dataclass
class MockMetadata:
    name: str


@dataclass
class MockEntry:
    metadata: MockMetadata
    source: str


def _unstyled(text: str) -> str:
    return click.unstyle(text)


# ── Scenario: Multi-install ────────────────────────────────────────────────────


def test_module_install_accepts_multiple_ids() -> None:
    """specfact module install A B must accept two positional arguments."""
    installed: list[str] = []

    def _fake_install(module_id: str, options: object | None = None, **_kwargs: object) -> Path:
        installed.append(module_id)
        return Path(f"/tmp/{module_id.split('/')[1]}")

    with (
        patch(
            "specfact_cli.modules.module_registry.src.commands.install_module",
            side_effect=_fake_install,
        ),
        patch(
            "specfact_cli.modules.module_registry.src.commands.discover_all_modules",
            return_value=[],
        ),
        patch(
            "specfact_cli.modules.module_registry.src.commands._install_skip_if_already_satisfied",
            return_value=False,
        ),
        patch(
            "specfact_cli.modules.module_registry.src.commands._try_install_bundled_module",
            return_value=False,
        ),
    ):
        result = runner.invoke(app, ["module", "install", "nold-ai/specfact-codebase", "nold-ai/specfact-code-review"])

    output = _unstyled(result.output)
    assert result.exit_code != 2, f"Exit code 2 = CLI arg error; got: {output}"
    assert "nold-ai/specfact-codebase" in installed or "specfact-codebase" in str(installed), (
        f"Both modules should be installed; installed={installed}"
    )
    assert "nold-ai/specfact-code-review" in installed or "specfact-code-review" in str(installed)


def test_module_install_rejects_version_with_multiple_module_ids() -> None:
    """--version is only valid with a single module id."""
    result = runner.invoke(
        app,
        [
            "module",
            "install",
            "nold-ai/specfact-codebase",
            "nold-ai/specfact-code-review",
            "--version",
            "1.0.0",
        ],
    )
    assert result.exit_code == 1
    out = _unstyled(result.output).lower()
    assert "single" in out and "version" in out


def test_module_install_single_still_works() -> None:
    """Single-module install must still work after multi-install change."""
    installed: list[str] = []

    def _fake_install(module_id: str, options: object | None = None, **_kwargs: object) -> Path:
        installed.append(module_id)
        return Path(f"/tmp/{module_id.split('/')[1]}")

    with (
        patch(
            "specfact_cli.modules.module_registry.src.commands.install_module",
            side_effect=_fake_install,
        ),
        patch(
            "specfact_cli.modules.module_registry.src.commands.discover_all_modules",
            return_value=[],
        ),
        patch(
            "specfact_cli.modules.module_registry.src.commands._install_skip_if_already_satisfied",
            return_value=False,
        ),
        patch(
            "specfact_cli.modules.module_registry.src.commands._try_install_bundled_module",
            return_value=False,
        ),
    ):
        result = runner.invoke(app, ["module", "install", "nold-ai/specfact-codebase"])

    assert result.exit_code != 2, f"Exit code 2 = CLI arg error: {_unstyled(result.output)}"
    assert len(installed) == 1


def test_module_install_multi_aborts_on_first_failure_without_installing_rest() -> None:
    """Multi-install: if module A fails, do not attempt B (avoid partial surprise state)."""
    installed: list[str] = []

    def _fake_install(module_id: str, options: object | None = None, **_kwargs: object) -> Path:
        if "codebase" in module_id:
            raise RuntimeError("mock install failure for first module")
        installed.append(module_id)
        return Path("/tmp/ok")

    with (
        patch(
            "specfact_cli.modules.module_registry.src.commands.install_module",
            side_effect=_fake_install,
        ),
        patch(
            "specfact_cli.modules.module_registry.src.commands.discover_all_modules",
            return_value=[],
        ),
        patch(
            "specfact_cli.modules.module_registry.src.commands._install_skip_if_already_satisfied",
            return_value=False,
        ),
        patch(
            "specfact_cli.modules.module_registry.src.commands._try_install_bundled_module",
            return_value=False,
        ),
    ):
        result = runner.invoke(
            app,
            ["module", "install", "nold-ai/specfact-codebase", "nold-ai/specfact-code-review"],
        )

    assert result.exit_code == 1
    assert installed == [], "Second module must not install after first fails"


def test_module_install_multi_skips_already_installed_and_continues() -> None:
    """Multi-install: if A is already installed, skip A but still install B; exit 0."""
    installed: list[str] = []

    def _fake_skip(*args: Any, **_kwargs: Any) -> bool:
        return "codebase" in str(args[1])  # A is already installed

    def _fake_install(module_id: str, options: object | None = None, **_kwargs: object) -> Path:
        installed.append(module_id)
        return Path(f"/tmp/{module_id.split('/')[1]}")

    with (
        patch(
            "specfact_cli.modules.module_registry.src.commands.install_module",
            side_effect=_fake_install,
        ),
        patch(
            "specfact_cli.modules.module_registry.src.commands.discover_all_modules",
            return_value=[],
        ),
        patch(
            "specfact_cli.modules.module_registry.src.commands._install_skip_if_already_satisfied",
            side_effect=_fake_skip,
        ),
        patch(
            "specfact_cli.modules.module_registry.src.commands._try_install_bundled_module",
            return_value=False,
        ),
    ):
        result = runner.invoke(app, ["module", "install", "nold-ai/specfact-codebase", "nold-ai/specfact-code-review"])

    assert result.exit_code == 0, f"Should exit 0 when only one is skipped: {_unstyled(result.output)}"
    assert any("code-review" in mid for mid in installed), "B must still be installed even if A was skipped"


# ── Scenario: Multi-uninstall ─────────────────────────────────────────────────


def test_module_uninstall_accepts_multiple_names() -> None:
    """specfact module uninstall A B must accept two positional arguments."""
    uninstalled: list[str] = []

    def _fake_uninstall(module_name: str, **kwargs: object) -> None:
        uninstalled.append(module_name)

    with (
        patch(
            "specfact_cli.modules.module_registry.src.commands.uninstall_module",
            side_effect=_fake_uninstall,
        ),
        patch(
            "specfact_cli.modules.module_registry.src.commands.discover_all_modules",
            return_value=[
                MockEntry(MockMetadata("specfact-codebase"), "marketplace"),
                MockEntry(MockMetadata("specfact-code-review"), "marketplace"),
            ],
        ),
    ):
        result = runner.invoke(app, ["module", "uninstall", "specfact-codebase", "specfact-code-review"])

    output = _unstyled(result.output)
    assert result.exit_code != 2, f"Exit code 2 = CLI arg error: {output}"


def test_module_uninstall_single_still_works() -> None:
    """Single-module uninstall must still work after multi-uninstall change."""
    with (
        patch("specfact_cli.modules.module_registry.src.commands.uninstall_module"),
        patch(
            "specfact_cli.modules.module_registry.src.commands.discover_all_modules",
            return_value=[
                MockEntry(MockMetadata("specfact-codebase"), "marketplace"),
            ],
        ),
    ):
        result = runner.invoke(app, ["module", "uninstall", "specfact-codebase"])

    assert result.exit_code != 2, f"Exit code 2 = CLI arg error: {_unstyled(result.output)}"


def test_module_uninstall_multi_missing_first_reports_error_still_uninstalls_rest_exits_nonzero(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """7c.7: If A is not installed, report error, still uninstall B, exit non-zero."""
    uninstalled: list[str] = []

    def _fake_uninstall(module_name: str, **kwargs: object) -> None:
        uninstalled.append(module_name)

    discovered = [
        MockEntry(MockMetadata("specfact-code-review"), "marketplace"),
    ]
    # The command probes the user module root before marketplace discovery.
    # A hosted runner can contain a real module from an earlier job, so isolate
    # that global process path to make the scenario deterministic.
    monkeypatch.setattr(
        "specfact_cli.modules.module_registry.src.commands.USER_MODULES_ROOT", tmp_path / "user-modules"
    )

    with (
        patch(
            "specfact_cli.modules.module_registry.src.commands.uninstall_module",
            side_effect=_fake_uninstall,
        ),
        patch(
            "specfact_cli.modules.module_registry.src.commands.discover_all_modules",
            return_value=discovered,
        ),
    ):
        result = runner.invoke(
            app,
            ["module", "uninstall", "specfact-codebase", "specfact-code-review"],
        )

    assert uninstalled == ["specfact-code-review"], (
        "Missing module must not block uninstall of remaining names; got "
        + repr(uninstalled)
        + "; CLI output: "
        + _unstyled(result.output)
    )
    assert result.exit_code == 1, "Overall exit must be non-zero when any name failed"
