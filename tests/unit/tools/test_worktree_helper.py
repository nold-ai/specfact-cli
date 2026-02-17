"""Tests for scripts/worktree.sh helper behavior."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / "scripts" / "worktree.sh"


def _run_helper(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["WORKTREE_DRY_RUN"] = "1"
    return subprocess.run(
        ["bash", str(SCRIPT_PATH), *command],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_rejects_protected_branch_dev(tmp_path: Path) -> None:
    """Create rejects protected branch names."""
    result = _run_helper(["create", "dev"], tmp_path)

    assert result.returncode != 0
    assert "protected branch" in result.stderr.lower()


def test_rejects_unsupported_branch_type(tmp_path: Path) -> None:
    """Create rejects unsupported branch families."""
    result = _run_helper(["create", "release/1.2.0"], tmp_path)

    assert result.returncode != 0
    assert "allowed branch types" in result.stderr.lower()


def test_create_uses_deterministic_path(tmp_path: Path) -> None:
    """Create computes deterministic worktree path from branch."""
    result = _run_helper(["create", "feature/abc-123-test-flow"], tmp_path)

    assert result.returncode == 0
    assert "specfact-cli-worktrees/feature/abc-123-test-flow" in result.stdout


def test_cleanup_prints_remove_and_prune_steps(tmp_path: Path) -> None:
    """Cleanup shows mapped remove and prune operations."""
    result = _run_helper(["cleanup", "feature/abc-123-test-flow"], tmp_path)

    assert result.returncode == 0
    assert "git worktree remove" in result.stdout
    assert "git worktree prune" in result.stdout
