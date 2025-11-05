"""Integration tests for enforce command."""

import os

from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.models.enforcement import EnforcementConfig
from specfact_cli.utils.yaml_utils import load_yaml


runner = CliRunner()


class TestEnforceStageCommand:
    """Test suite for enforce stage command."""

    def test_enforce_stage_balanced_preset(self, tmp_path):
        """Test setting balanced enforcement preset."""
        # Change to temp directory
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                app,
                [
                    "enforce",
                    "stage",
                    "--preset",
                    "balanced",
                ],
            )
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "Setting enforcement mode: balanced" in result.stdout
        assert "Enforcement mode set to balanced" in result.stdout

        # Verify config file was created
        config_path = tmp_path / ".specfact" / "gates" / "config" / "enforcement.yaml"
        assert config_path.exists()

        # Verify config content
        config_data = load_yaml(config_path)
        config = EnforcementConfig(**config_data)

        assert config.preset.value == "balanced"
        assert config.high_action.value == "BLOCK"
        assert config.medium_action.value == "WARN"
        assert config.low_action.value == "LOG"
        assert config.enabled is True

    def test_enforce_stage_strict_preset(self, tmp_path):
        """Test setting strict enforcement preset."""
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                app,
                [
                    "enforce",
                    "stage",
                    "--preset",
                    "strict",
                ],
            )
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "Setting enforcement mode: strict" in result.stdout

        # Verify config file
        config_path = tmp_path / ".specfact" / "gates" / "config" / "enforcement.yaml"
        assert config_path.exists()

        config_data = load_yaml(config_path)
        config = EnforcementConfig(**config_data)

        assert config.preset.value == "strict"
        assert config.high_action.value == "BLOCK"
        assert config.medium_action.value == "BLOCK"
        assert config.low_action.value == "WARN"

    def test_enforce_stage_minimal_preset(self, tmp_path):
        """Test setting minimal enforcement preset."""
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                app,
                [
                    "enforce",
                    "stage",
                    "--preset",
                    "minimal",
                ],
            )
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "Setting enforcement mode: minimal" in result.stdout

        # Verify config file
        config_path = tmp_path / ".specfact" / "gates" / "config" / "enforcement.yaml"
        assert config_path.exists()

        config_data = load_yaml(config_path)
        config = EnforcementConfig(**config_data)

        assert config.preset.value == "minimal"
        assert config.high_action.value == "WARN"
        assert config.medium_action.value == "WARN"
        assert config.low_action.value == "LOG"

    def test_enforce_stage_invalid_preset(self, tmp_path):
        """Test handling of invalid preset."""
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                app,
                [
                    "enforce",
                    "stage",
                    "--preset",
                    "invalid",
                ],
            )
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 1
        assert "Unknown preset: invalid" in result.stdout
        assert "Valid presets: minimal, balanced, strict" in result.stdout

    def test_enforce_stage_creates_structure(self, tmp_path):
        """Test that enforce stage creates .specfact structure."""
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                app,
                [
                    "enforce",
                    "stage",
                    "--preset",
                    "balanced",
                ],
            )
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0

        # Verify structure was created
        assert (tmp_path / ".specfact").exists()
        assert (tmp_path / ".specfact" / "gates").exists()
        assert (tmp_path / ".specfact" / "gates" / "config").exists()

    def test_enforce_stage_overwrites_existing_config(self, tmp_path):
        """Test that enforce stage overwrites existing config."""
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Set initial config
            result1 = runner.invoke(
                app,
                ["enforce", "stage", "--preset", "minimal"],
            )
            assert result1.exit_code == 0

            config_path = tmp_path / ".specfact" / "gates" / "config" / "enforcement.yaml"
            initial_config = load_yaml(config_path)
            assert initial_config["preset"] == "minimal"

            # Overwrite with new config
            result2 = runner.invoke(
                app,
                ["enforce", "stage", "--preset", "strict"],
            )
            assert result2.exit_code == 0
        finally:
            os.chdir(old_cwd)

        updated_config = load_yaml(config_path)
        assert updated_config["preset"] == "strict"
        assert updated_config["high_action"] == "BLOCK"
        assert updated_config["medium_action"] == "BLOCK"

    def test_enforce_stage_output_format(self, tmp_path):
        """Test that enforce stage displays proper table output."""
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                app,
                ["enforce", "stage", "--preset", "balanced"],
            )
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        # Check table components (with flexible spacing for Rich table formatting)
        assert "Enforcement Mode" in result.stdout
        assert "BALANCED" in result.stdout
        assert "HIGH" in result.stdout
        assert "MEDIUM" in result.stdout
        assert "LOW" in result.stdout
        assert "BLOCK" in result.stdout
        assert "WARN" in result.stdout
        assert "LOG" in result.stdout
