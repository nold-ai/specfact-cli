"""Integration checks for scripts/check_local_version_ahead_of_pypi.py (subprocess / filesystem)."""

from __future__ import annotations

import os
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest


def _project_version_from_pyproject_bytes(content: bytes) -> str:
    return tomllib.loads(content.decode("utf-8"))["project"]["version"].strip()


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
    local_version = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"].strip()
    head_pyproject = subprocess.run(
        ["git", "show", "HEAD:pyproject.toml"],
        check=False,
        capture_output=True,
        cwd=str(repo_root),
        timeout=30,
    )
    if head_pyproject.returncode != 0:
        pytest.skip("HEAD:pyproject.toml unavailable in this checkout")
    head_version = _project_version_from_pyproject_bytes(head_pyproject.stdout)
    if local_version != head_version:
        pytest.skip(f"working tree version {local_version!r} differs from HEAD {head_version!r}")

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
