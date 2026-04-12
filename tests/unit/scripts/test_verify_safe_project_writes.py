"""Tests for scripts/verify_safe_project_writes.py."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_verify_safe_project_writes_passes_on_repo() -> None:
    """Gate must succeed while ide_setup routes settings through project_artifact_write."""
    script = Path(__file__).resolve().parents[3] / "scripts" / "verify_safe_project_writes.py"
    completed = subprocess.run(
        [sys.executable, str(script)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
