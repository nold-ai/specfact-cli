"""Integration checks for scripts/check_local_version_ahead_of_pypi.py (subprocess / filesystem)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.integration
def test_script_exits_zero_when_skip_env() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    script = repo_root / "scripts" / "check_local_version_ahead_of_pypi.py"
    env = os.environ.copy()
    env["SPECFACT_SKIP_PYPI_VERSION_CHECK"] = "1"
    completed = subprocess.run(
        [sys.executable, str(script)],
        check=False,
        capture_output=True,
        text=True,
        env=env,
        cwd=str(repo_root),
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr


@pytest.mark.integration
def test_script_exits_zero_skip_when_version_matches_head_without_skip_env() -> None:
    """Clean trees match HEAD; skip path avoids PyPI (no lenient network needed)."""
    repo_root = Path(__file__).resolve().parents[3]
    script = repo_root / "scripts" / "check_local_version_ahead_of_pypi.py"
    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            "--skip-when-version-unchanged-vs",
            "HEAD",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(repo_root),
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    assert "skipped PyPI query" in completed.stderr
