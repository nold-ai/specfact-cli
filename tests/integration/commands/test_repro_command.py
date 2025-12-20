"""Integration tests for repro command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from specfact_cli.cli import app


runner = CliRunner()


class TestReproSetupCommand:
    """Test suite for repro setup command."""

    def test_setup_creates_pyproject_toml_with_crosshair_config(self, tmp_path: Path, monkeypatch):
        """Test setup creates pyproject.toml with CrossHair configuration."""
        monkeypatch.chdir(tmp_path)

        # Create minimal project structure
        src_dir = tmp_path / "src" / "test_package"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")

        result = runner.invoke(app, ["repro", "setup", "--repo", str(tmp_path)])

        assert result.exit_code == 0
        assert "Setting up CrossHair configuration" in result.stdout
        assert "Setup complete!" in result.stdout

        # Verify pyproject.toml was created
        pyproject_path = tmp_path / "pyproject.toml"
        assert pyproject_path.exists()

        # Verify CrossHair config exists
        content = pyproject_path.read_text()
        assert "[tool.crosshair]" in content
        assert "timeout = 60" in content
        assert "per_condition_timeout = 10" in content
        assert "per_path_timeout = 5" in content
        assert "max_iterations = 1000" in content

    def test_setup_updates_existing_pyproject_toml(self, tmp_path: Path, monkeypatch):
        """Test setup updates existing pyproject.toml with CrossHair configuration."""
        monkeypatch.chdir(tmp_path)

        # Create existing pyproject.toml
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_text(
            """[project]
name = "test-package"
version = "0.1.0"
"""
        )

        # Create source directory
        src_dir = tmp_path / "src" / "test_package"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")

        result = runner.invoke(app, ["repro", "setup", "--repo", str(tmp_path)])

        assert result.exit_code == 0
        assert "Updated pyproject.toml" in result.stdout

        # Verify existing content is preserved
        content = pyproject_path.read_text()
        assert "[project]" in content
        assert 'name = "test-package"' in content

        # Verify CrossHair config was added
        assert "[tool.crosshair]" in content
        assert "timeout = 60" in content

    def test_setup_updates_existing_crosshair_config(self, tmp_path: Path, monkeypatch):
        """Test setup updates existing CrossHair configuration."""
        monkeypatch.chdir(tmp_path)

        # Create pyproject.toml with existing CrossHair config
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_text(
            """[project]
name = "test-package"

[tool.crosshair]
timeout = 30
per_condition_timeout = 5
"""
        )

        src_dir = tmp_path / "src" / "test_package"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")

        result = runner.invoke(app, ["repro", "setup", "--repo", str(tmp_path)])

        assert result.exit_code == 0

        # Verify config was updated to standard values
        content = pyproject_path.read_text()
        assert "[tool.crosshair]" in content
        assert "timeout = 60" in content  # Updated
        assert "per_condition_timeout = 10" in content  # Updated
        assert "per_path_timeout = 5" in content  # Added
        assert "max_iterations = 1000" in content  # Added

    def test_setup_detects_hatch_environment(self, tmp_path: Path, monkeypatch):
        """Test setup detects hatch environment manager."""
        monkeypatch.chdir(tmp_path)

        # Create hatch project
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_text(
            """[project]
name = "test-package"

[tool.hatch.build.targets.wheel]
packages = ["src/test_package"]
"""
        )

        src_dir = tmp_path / "src" / "test_package"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")

        result = runner.invoke(app, ["repro", "setup", "--repo", str(tmp_path)])

        assert result.exit_code == 0
        assert "hatch" in result.stdout.lower() or "Detected" in result.stdout

    def test_setup_detects_poetry_environment(self, tmp_path: Path, monkeypatch):
        """Test setup detects poetry environment manager."""
        monkeypatch.chdir(tmp_path)

        # Create poetry project
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_text(
            """[tool.poetry]
name = "test-package"
version = "0.1.0"
"""
        )

        src_dir = tmp_path / "src" / "test_package"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")

        result = runner.invoke(app, ["repro", "setup", "--repo", str(tmp_path)])

        assert result.exit_code == 0
        # Should complete successfully regardless of poetry detection

    def test_setup_detects_source_directories(self, tmp_path: Path, monkeypatch):
        """Test setup detects source directories correctly."""
        monkeypatch.chdir(tmp_path)

        # Create src/ structure
        src_dir = tmp_path / "src" / "test_package"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")

        result = runner.invoke(app, ["repro", "setup", "--repo", str(tmp_path)])

        assert result.exit_code == 0
        assert "Detected source directories" in result.stdout
        assert "src/" in result.stdout

    def test_setup_detects_lib_directory(self, tmp_path: Path, monkeypatch):
        """Test setup detects lib/ directory."""
        monkeypatch.chdir(tmp_path)

        # Create lib/ structure
        lib_dir = tmp_path / "lib" / "test_package"
        lib_dir.mkdir(parents=True)
        (lib_dir / "__init__.py").write_text("")

        result = runner.invoke(app, ["repro", "setup", "--repo", str(tmp_path)])

        assert result.exit_code == 0
        assert "Detected source directories" in result.stdout
        assert "lib/" in result.stdout

    def test_setup_handles_no_source_directories(self, tmp_path: Path, monkeypatch):
        """Test setup handles repositories without standard source directories."""
        monkeypatch.chdir(tmp_path)

        # Create root-level Python file
        (tmp_path / "module.py").write_text("def hello(): pass")

        result = runner.invoke(app, ["repro", "setup", "--repo", str(tmp_path)])

        assert result.exit_code == 0
        # Should still complete successfully, using "." as fallback

    @patch("specfact_cli.commands.repro.check_tool_in_env")
    def test_setup_warns_when_crosshair_not_available(self, mock_check_tool, tmp_path: Path, monkeypatch):
        """Test setup warns when crosshair-tool is not available."""
        monkeypatch.chdir(tmp_path)

        # Mock crosshair as not available
        mock_check_tool.return_value = (False, "Tool 'crosshair' not found")

        src_dir = tmp_path / "src" / "test_package"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")

        result = runner.invoke(app, ["repro", "setup", "--repo", str(tmp_path)])

        assert result.exit_code == 0
        assert "crosshair-tool not available" in result.stdout
        assert "Tip:" in result.stdout

    @patch("specfact_cli.commands.repro.check_tool_in_env")
    def test_setup_shows_crosshair_available(self, mock_check_tool, tmp_path: Path, monkeypatch):
        """Test setup shows success when crosshair-tool is available."""
        monkeypatch.chdir(tmp_path)

        # Mock crosshair as available
        mock_check_tool.return_value = (True, None)

        src_dir = tmp_path / "src" / "test_package"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")

        result = runner.invoke(app, ["repro", "setup", "--repo", str(tmp_path)])

        assert result.exit_code == 0
        assert "crosshair-tool is available" in result.stdout

    @patch("subprocess.run")
    @patch("specfact_cli.commands.repro.check_tool_in_env")
    def test_setup_installs_crosshair_when_requested(
        self, mock_check_tool, mock_subprocess, tmp_path: Path, monkeypatch
    ):
        """Test setup attempts to install crosshair-tool when --install-crosshair is used."""
        monkeypatch.chdir(tmp_path)

        # Mock crosshair as not available
        mock_check_tool.return_value = (False, "Tool 'crosshair' not found")

        # Mock successful installation
        mock_proc = type("MockProc", (), {"returncode": 0, "stderr": ""})()
        mock_subprocess.return_value = mock_proc

        src_dir = tmp_path / "src" / "test_package"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")

        result = runner.invoke(app, ["repro", "setup", "--repo", str(tmp_path), "--install-crosshair"])

        assert result.exit_code == 0
        assert "Attempting to install crosshair-tool" in result.stdout
        mock_subprocess.assert_called_once()

    @patch("subprocess.run")
    @patch("specfact_cli.commands.repro.check_tool_in_env")
    def test_setup_handles_installation_failure(self, mock_check_tool, mock_subprocess, tmp_path: Path, monkeypatch):
        """Test setup handles crosshair-tool installation failure gracefully."""
        monkeypatch.chdir(tmp_path)

        # Mock crosshair as not available
        mock_check_tool.return_value = (False, "Tool 'crosshair' not found")

        # Mock failed installation
        mock_proc = type("MockProc", (), {"returncode": 1, "stderr": "Installation failed"})()
        mock_subprocess.return_value = mock_proc

        src_dir = tmp_path / "src" / "test_package"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")

        result = runner.invoke(app, ["repro", "setup", "--repo", str(tmp_path), "--install-crosshair"])

        assert result.exit_code == 0  # Setup still succeeds even if installation fails
        assert "Failed to install crosshair-tool" in result.stdout

    def test_setup_provides_installation_guidance_for_hatch(self, tmp_path: Path, monkeypatch):
        """Test setup provides hatch-specific installation guidance."""
        monkeypatch.chdir(tmp_path)

        # Create hatch project
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_text(
            """[project]
name = "test-package"

[tool.hatch.build.targets.wheel]
packages = ["src/test_package"]
"""
        )

        src_dir = tmp_path / "src" / "test_package"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")

        with patch("specfact_cli.commands.repro.check_tool_in_env") as mock_check:
            mock_check.return_value = (False, "Tool 'crosshair' not found")

            result = runner.invoke(app, ["repro", "setup", "--repo", str(tmp_path)])

            assert result.exit_code == 0
            # Should mention hatch in installation guidance
            assert "hatch" in result.stdout.lower() or "Install" in result.stdout

    def test_setup_shows_next_steps(self, tmp_path: Path, monkeypatch):
        """Test setup shows helpful next steps after completion."""
        monkeypatch.chdir(tmp_path)

        src_dir = tmp_path / "src" / "test_package"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")

        result = runner.invoke(app, ["repro", "setup", "--repo", str(tmp_path)])

        assert result.exit_code == 0
        assert "Next steps:" in result.stdout
        assert "specfact repro" in result.stdout
        assert "CrossHair will automatically explore contracts" in result.stdout

    def test_setup_fails_gracefully_on_pyproject_write_error(self, tmp_path: Path, monkeypatch):
        """Test setup handles pyproject.toml write errors gracefully."""
        monkeypatch.chdir(tmp_path)

        src_dir = tmp_path / "src" / "test_package"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")

        # Make pyproject.toml directory unwritable
        pyproject_path = tmp_path / "pyproject.toml"
        if pyproject_path.exists():
            pyproject_path.chmod(0o000)
        else:
            # Create a directory with same name to cause write error
            pyproject_path.mkdir()
            pyproject_path.chmod(0o555)

        try:
            result = runner.invoke(app, ["repro", "setup", "--repo", str(tmp_path)])

            # Should fail with error message
            assert result.exit_code == 1
            assert "Failed to update" in result.stdout or "Error" in result.stdout
        finally:
            # Clean up permissions
            if pyproject_path.exists():
                try:
                    if pyproject_path.is_dir():
                        pyproject_path.rmdir()
                    else:
                        pyproject_path.chmod(0o644)
                except Exception:
                    pass
