"""Tests for scripts/export-change-to-github.py wrapper script."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path
from typing import Any

import pytest



def _load_script_module() -> Any:
    """Load scripts/export-change-to-github.py as a Python module."""
    script_path = Path(__file__).resolve().parents[3] / "scripts" / "export-change-to-github.py"
    spec = importlib.util.spec_from_file_location("export_change_to_github", script_path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load script module at {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_command_with_inplace_update_sets_update_existing() -> None:
    """--inplace-update should map to sync bridge --update-existing."""
    module = _load_script_module()

    command = module.build_export_command(
        repo=Path("/repo"),
        change_ids=["module-migration-03-core-slimming"],
        repo_owner="nold-ai",
        repo_name="specfact-cli",
        inplace_update=True,
    )

    assert command[:7] == [
        "specfact",
        "project",
        "sync",
        "bridge",
        "--adapter",
        "github",
        "--mode",
    ]
    assert "export-only" in command
    assert "export-only" in command
    assert "--change-ids" in command
    assert "module-migration-03-core-slimming" in command
    assert "--update-existing" in command


def test_build_command_without_inplace_update_omits_update_existing() -> None:
    """Without --inplace-update, wrapper must not force --update-existing."""
    module = _load_script_module()

    command = module.build_export_command(
        repo=Path("/repo"),
        change_ids=["module-migration-03-core-slimming"],
        repo_owner=None,
        repo_name=None,
        inplace_update=False,
    )

    assert "--update-existing" not in command


def test_main_invokes_subprocess_with_expected_command(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() should execute the built sync command and return exit code 0 on success."""
    module = _load_script_module()

    captured: list[list[str]] = []

    def _fake_run(cmd: list[str], check: bool) -> subprocess.CompletedProcess[str]:
        captured.append(cmd)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(module.subprocess, "run", _fake_run)

    exit_code = module.main(
        [
            "--change-id",
            "module-migration-03-core-slimming",
            "--repo",
            "/repo",
            "--inplace-update",
        ]
    )

    assert exit_code == 0
    assert captured, "expected subprocess.run to be called"
    assert "--update-existing" in captured[0]
    assert "--change-ids" in captured[0]


def test_main_returns_subprocess_exit_code(monkeypatch: pytest.MonkeyPatch) -> None:
    """Wrapper should propagate non-zero sync exit code."""
    module = _load_script_module()

    def _fake_run(cmd: list[str], check: bool) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(cmd, 2)

    monkeypatch.setattr(module.subprocess, "run", _fake_run)

    exit_code = module.main(
        [
            "--change-id",
            "module-migration-03-core-slimming",
            "--repo",
            "/repo",
        ]
    )

    assert exit_code == 2
