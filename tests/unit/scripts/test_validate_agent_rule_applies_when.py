"""Tests for scripts/validate_agent_rule_applies_when.py."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_validate_agent_rule_applies_when_passes() -> None:
    script = Path(__file__).resolve().parents[3] / "scripts" / "validate_agent_rule_applies_when.py"
    completed = subprocess.run(
        [sys.executable, str(script)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
