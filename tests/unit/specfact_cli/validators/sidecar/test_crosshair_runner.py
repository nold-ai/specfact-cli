"""
Unit tests for CrossHair runner.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from specfact_cli.validators.sidecar.crosshair_runner import CrosshairRunOptions, run_crosshair


def test_run_crosshair_not_found(tmp_path: Path) -> None:
    """Test CrossHair runner when CrossHair is not found."""
    source_path = tmp_path / "test.py"
    source_path.write_text("def test(): pass\n")

    with patch("subprocess.run", side_effect=FileNotFoundError()):
        result = run_crosshair(source_path, CrosshairRunOptions(timeout=10))
        assert result["success"] is False
        assert "not found" in result["stderr"]


def test_run_crosshair_timeout(tmp_path: Path) -> None:
    """Test CrossHair runner timeout handling."""
    source_path = tmp_path / "test.py"
    source_path.write_text("def test(): pass\n")

    from subprocess import TimeoutExpired

    with patch("subprocess.run", side_effect=TimeoutExpired(cmd=["crosshair"], timeout=10)):
        result = run_crosshair(source_path, CrosshairRunOptions(timeout=10))
        assert result["success"] is False
        assert "timed out" in result["stderr"]


def test_run_crosshair_success(tmp_path: Path) -> None:
    """Test CrossHair runner successful execution."""
    source_path = tmp_path / "test.py"
    source_path.write_text("def test(): pass\n")

    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = "No issues found"
    mock_proc.stderr = ""

    with patch("subprocess.run", return_value=mock_proc):
        result = run_crosshair(source_path, CrosshairRunOptions(timeout=10))
        assert result["success"] is True
        assert result["returncode"] == 0
