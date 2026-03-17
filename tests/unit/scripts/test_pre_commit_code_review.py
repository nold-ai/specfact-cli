"""Tests for scripts/pre_commit_code_review.py."""

# pyright: reportUnknownMemberType=false

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest


def _load_script_module() -> Any:
    """Load scripts/pre_commit_code_review.py as a Python module."""
    script_path = Path(__file__).resolve().parents[3] / "scripts" / "pre_commit_code_review.py"
    spec = importlib.util.spec_from_file_location("pre_commit_code_review", script_path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load script module at {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_filter_review_files_keeps_only_python_sources() -> None:
    """Only relevant staged Python files should be reviewed."""
    module = _load_script_module()

    assert module.filter_review_files(["src/app.py", "README.md", "tests/test_app.py", "notes.txt"]) == [
        "src/app.py",
        "tests/test_app.py",
    ]


def test_build_review_command_uses_score_only_mode() -> None:
    """Pre-commit gate should rely on score-only exit-code semantics."""
    module = _load_script_module()

    command = module.build_review_command(["src/app.py", "tests/test_app.py"])

    assert command[:5] == [sys.executable, "-m", "specfact_cli.cli", "code", "review"]
    assert "--score-only" in command
    assert command[-2:] == ["src/app.py", "tests/test_app.py"]


def test_main_skips_when_no_relevant_files(capsys: pytest.CaptureFixture[str]) -> None:
    """Hook should not fail commits when no staged Python files are present."""
    module = _load_script_module()

    exit_code = module.main(["README.md", "docs/guide.md"])

    assert exit_code == 0
    assert "No staged Python files" in capsys.readouterr().out


def test_main_propagates_review_gate_exit_code(monkeypatch: pytest.MonkeyPatch) -> None:
    """Blocking review verdicts must block the commit by returning non-zero."""
    module = _load_script_module()

    def _fake_ensure() -> tuple[bool, str | None]:
        return True, None

    def _fake_run(cmd: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        assert "--score-only" in cmd
        return subprocess.CompletedProcess(cmd, 1, stdout="-7\n", stderr="")

    monkeypatch.setattr(module, "ensure_runtime_available", _fake_ensure)
    monkeypatch.setattr(module.subprocess, "run", _fake_run)

    exit_code = module.main(["src/app.py"])

    assert exit_code == 1


def test_main_prints_actionable_setup_guidance_when_runtime_missing(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Missing review runtime should fail with actionable setup guidance."""
    module = _load_script_module()

    def _fake_ensure() -> tuple[bool, str | None]:
        return False, 'Install dev dependencies with `pip install -e ".[dev]"` or run `hatch env create`.'

    monkeypatch.setattr(module, "ensure_runtime_available", _fake_ensure)

    exit_code = module.main(["src/app.py"])

    assert exit_code == 1
    assert "Install dev dependencies" in capsys.readouterr().out
