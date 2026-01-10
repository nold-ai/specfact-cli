"""
Unit tests for Specmatic runner.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from specfact_cli.validators.sidecar.specmatic_runner import run_specmatic


def test_run_specmatic_not_found(tmp_path: Path) -> None:
    """Test Specmatic runner when Specmatic is not found."""
    contract_path = tmp_path / "contract.yaml"
    contract_path.write_text("openapi: 3.0.3\n")

    with patch("subprocess.run", side_effect=FileNotFoundError()):
        result = run_specmatic(contract_path, timeout=10)
        assert result["success"] is False
        assert "not found" in result["stderr"]


def test_run_specmatic_timeout(tmp_path: Path) -> None:
    """Test Specmatic runner timeout handling."""
    contract_path = tmp_path / "contract.yaml"
    contract_path.write_text("openapi: 3.0.3\n")

    from subprocess import TimeoutExpired

    with patch("subprocess.run", side_effect=TimeoutExpired(cmd=["specmatic"], timeout=10)):
        result = run_specmatic(contract_path, timeout=10)
        assert result["success"] is False
        assert "timed out" in result["stderr"]


def test_run_specmatic_success(tmp_path: Path) -> None:
    """Test Specmatic runner successful execution."""
    contract_path = tmp_path / "contract.yaml"
    contract_path.write_text("openapi: 3.0.3\n")

    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = "All tests passed"
    mock_proc.stderr = ""

    with patch("subprocess.run", return_value=mock_proc):
        result = run_specmatic(contract_path, timeout=10)
        assert result["success"] is True
        assert result["returncode"] == 0
