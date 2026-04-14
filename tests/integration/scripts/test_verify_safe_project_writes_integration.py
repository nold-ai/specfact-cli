"""Integration: verify_safe_project_writes against the real repository ide_setup.py."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.integration
def test_verify_safe_project_writes_passes_on_repo() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    script = repo_root / "scripts" / "verify_safe_project_writes.py"
    completed = subprocess.run(
        [sys.executable, str(script)],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(repo_root),
    )
    assert completed.returncode == 0, completed.stderr
