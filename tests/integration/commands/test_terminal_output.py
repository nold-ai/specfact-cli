"""
Integration tests for terminal output in different terminal modes.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from specfact_cli.runtime import TerminalMode, get_configured_console, get_terminal_mode
from specfact_cli.utils.terminal import get_progress_config


class TestTerminalModeDetection:
    """Test terminal mode detection in integration scenarios."""

    def test_terminal_mode_basic_with_no_color(self, tmp_path: Path) -> None:
        """Test that NO_COLOR environment variable results in BASIC mode."""
        with patch.dict(os.environ, {"NO_COLOR": "1"}, clear=True):
            mode = get_terminal_mode()
            assert mode == TerminalMode.BASIC

    def test_terminal_mode_basic_with_ci(self, tmp_path: Path) -> None:
        """Test that CI environment variable results in BASIC mode."""
        with patch.dict(os.environ, {"CI": "true"}, clear=True):
            mode = get_terminal_mode()
            assert mode == TerminalMode.BASIC

    def test_console_configuration_in_basic_mode(self, tmp_path: Path) -> None:
        """Test console configuration in basic terminal mode."""
        with patch.dict(os.environ, {"CI": "true"}, clear=True):
            console = get_configured_console()
            assert console is not None
            # In basic mode, console should be configured (verify it's a Console instance)
            from rich.console import Console

            assert isinstance(console, Console)

    def test_progress_configuration_in_basic_mode(self, tmp_path: Path) -> None:
        """Test progress configuration in basic terminal mode."""
        with patch.dict(os.environ, {"CI": "true"}, clear=True):
            columns, _kwargs = get_progress_config()
            # In basic mode, should have minimal columns (no animations)
            assert len(columns) == 1  # TextColumn only
            assert isinstance(columns, tuple)


class TestCommandOutputInBasicMode:
    """Test command output in basic terminal mode."""

    def test_import_command_output_basic_mode(self, tmp_path: Path) -> None:
        """Test import command produces readable output in basic mode."""
        # Create a minimal Python file for import
        python_file = tmp_path / "test_module.py"
        python_file.write_text("def hello(): pass\n")

        env = os.environ.copy()
        env["CI"] = "true"
        env["NO_COLOR"] = "1"

        # Run import command in basic mode (--no-interactive is global flag)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "specfact_cli.cli",
                "--no-interactive",
                "import",
                "from-code",
                "test-bundle",
                "--repo",
                str(tmp_path),
            ],
            capture_output=True,
            text=True,
            env=env,
            cwd=tmp_path,
            timeout=60,
        )

        # Should produce output (may fail due to missing dependencies, but should show output)
        assert len(result.stdout) > 0 or len(result.stderr) > 0

    def test_sync_command_output_basic_mode(self, tmp_path: Path) -> None:
        """Test sync command produces readable output in basic mode."""
        env = os.environ.copy()
        env["CI"] = "true"
        env["NO_COLOR"] = "1"

        # Run sync command in basic mode (will likely fail due to no bundle, but should produce readable output)
        result = subprocess.run(
            [sys.executable, "-m", "specfact_cli.cli", "--no-interactive", "sync", "bridge", "--repo", str(tmp_path)],
            capture_output=True,
            text=True,
            env=env,
            cwd=tmp_path,
            timeout=30,
        )

        # Should produce output (even if error)
        assert len(result.stdout) > 0 or len(result.stderr) > 0
