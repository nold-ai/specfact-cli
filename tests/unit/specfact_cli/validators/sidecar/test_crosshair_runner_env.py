"""
Unit tests for CrossHair runner environment variable handling.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from specfact_cli.validators.sidecar.crosshair_runner import run_crosshair


class TestCrosshairRunnerEnvironment:
    """Test environment variable preservation in CrossHair runner."""

    def test_preserves_path_environment(self) -> None:
        """Test that PATH is preserved when running CrossHair."""
        test_file = Path("/tmp/test_file.py")
        test_file.write_text("def test(): pass")

        try:
            original_path = os.environ.get("PATH", "")

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="", text=True)

                run_crosshair(test_file, timeout=10)

                # Verify subprocess.run was called
                assert mock_run.called

                # Get the env dict passed to subprocess.run
                call_kwargs = mock_run.call_args[1]
                env = call_kwargs.get("env", {})

                # PATH should be preserved
                assert "PATH" in env
                assert env["PATH"] == original_path

        finally:
            test_file.unlink(missing_ok=True)

    def test_adds_pythonpath_when_provided(self) -> None:
        """Test that PYTHONPATH is added when provided."""
        test_file = Path("/tmp/test_file.py")
        test_file.write_text("def test(): pass")

        try:
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="", text=True)

                custom_pythonpath = "/custom/path"
                run_crosshair(test_file, timeout=10, pythonpath=custom_pythonpath)

                # Get the env dict passed to subprocess.run
                call_kwargs = mock_run.call_args[1]
                env = call_kwargs.get("env", {})

                # PYTHONPATH should be set
                assert "PYTHONPATH" in env
                assert env["PYTHONPATH"] == custom_pythonpath

                # PATH should still be preserved
                assert "PATH" in env

        finally:
            test_file.unlink(missing_ok=True)

    def test_preserves_other_environment_variables(self) -> None:
        """Test that other environment variables are preserved."""
        test_file = Path("/tmp/test_file.py")
        test_file.write_text("def test(): pass")

        try:
            # Set a test environment variable
            os.environ["TEST_VAR"] = "test_value"

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="", text=True)

                run_crosshair(test_file, timeout=10)

                # Get the env dict passed to subprocess.run
                call_kwargs = mock_run.call_args[1]
                env = call_kwargs.get("env", {})

                # Test variable should be preserved
                assert "TEST_VAR" in env
                assert env["TEST_VAR"] == "test_value"

        finally:
            test_file.unlink(missing_ok=True)
            os.environ.pop("TEST_VAR", None)
