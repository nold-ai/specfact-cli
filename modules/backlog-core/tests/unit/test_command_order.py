"""Unit tests for backlog-core command ordering in help output."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from typer.testing import CliRunner


# ruff: noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "modules" / "backlog-core" / "src"))
sys.path.insert(0, str(REPO_ROOT / "src"))

from backlog_core.main import backlog_app


runner = CliRunner()


def _find_line(lines: list[str], needle: str) -> int:
    pattern = re.compile(rf"^\s*│\s+{re.escape(needle)}(?:\s{{2,}}|\\s*$)")
    for idx, line in enumerate(lines):
        if pattern.search(line):
            return idx
    return -1


def test_backlog_core_help_lists_command_groups_before_leaf_commands() -> None:
    """`backlog --help` lists grouped commands before leaf commands for discoverability."""
    result = runner.invoke(backlog_app, ["--help"])
    assert result.exit_code == 0

    lines = result.stdout.splitlines()
    delta_idx = _find_line(lines, "delta")
    sync_idx = _find_line(lines, "sync")
    verify_idx = _find_line(lines, "verify-readiness")

    assert delta_idx != -1
    assert sync_idx != -1
    assert verify_idx != -1
    assert delta_idx < sync_idx
    assert delta_idx < verify_idx
