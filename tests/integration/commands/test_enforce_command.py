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


class TestEnforceSddCommand:
    """Test suite for enforce sdd command."""

    def test_enforce_sdd_validates_hash_match(self, tmp_path, monkeypatch):
        """Test enforce sdd validates hash match between SDD and plan."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        # Create a plan and harden it
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        runner.invoke(app, ["plan", "harden", bundle_name, "--no-interactive"])

        # Enforce SDD validation
        result = runner.invoke(app, ["enforce", "sdd", bundle_name, "--no-interactive"])

        assert result.exit_code == 0
        assert "Hash match verified" in result.stdout or "validation" in result.stdout.lower()
        assert "SDD validation passed" in result.stdout or "validation" in result.stdout.lower()

        # Verify report was created (bundle-specific location)
        from specfact_cli.utils.structure import SpecFactStructure

        reports_dir = SpecFactStructure.get_bundle_reports_dir(bundle_name, tmp_path) / "enforcement"
        assert reports_dir.exists()
        report_files = list(reports_dir.glob("report-*.yaml"))
        assert len(report_files) > 0

    def test_enforce_sdd_detects_hash_mismatch(self, tmp_path, monkeypatch):
        """Test enforce sdd detects hash mismatch."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        # Create a plan and harden it
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        runner.invoke(app, ["plan", "harden", bundle_name, "--no-interactive"])

        # Modify the plan bundle hash in the SDD manifest directly to simulate a mismatch
        # This is more reliable than modifying the plan YAML, which might not change the hash
        from specfact_cli.utils.structure import SpecFactStructure
        from specfact_cli.utils.structured_io import StructuredFormat, dump_structured_file, load_structured_file

        sdd_path = SpecFactStructure.get_bundle_sdd_path(bundle_name, tmp_path, StructuredFormat.YAML)

        sdd_data = load_structured_file(sdd_path)
        # Change the hash to a different value to simulate mismatch
        original_hash = sdd_data["plan_bundle_hash"]
        sdd_data["plan_bundle_hash"] = "different_hash_" + "x" * (len(original_hash) - len("different_hash_"))
        dump_structured_file(sdd_data, sdd_path, StructuredFormat.YAML)

        # Enforce SDD validation (should detect mismatch)
        result = runner.invoke(app, ["enforce", "sdd", bundle_name, "--no-interactive"])

        # Hash mismatch should be detected (HIGH severity deviation)
        assert result.exit_code == 1, "Hash mismatch should cause exit code 1"
        assert "Hash mismatch" in result.stdout or "✗" in result.stdout or "mismatch" in result.stdout.lower()
        assert "SDD validation failed" in result.stdout or "validation" in result.stdout.lower()

    def test_enforce_sdd_validates_coverage_thresholds(self, tmp_path, monkeypatch):
        """Test enforce sdd validates coverage thresholds."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        # Create a plan with features and stories
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        runner.invoke(
            app,
            [
                "plan",
                "add-feature",
                "--key",
                "FEATURE-001",
                "--title",
                "Test Feature",
                "--acceptance",
                "Test acceptance",
                "--bundle",
                bundle_name,
            ],
        )
        runner.invoke(
            app,
            [
                "plan",
                "add-story",
                "--feature",
                "FEATURE-001",
                "--key",
                "STORY-001",
                "--title",
                "Test Story",
                "--bundle",
                bundle_name,
            ],
        )

        # Harden the plan
        runner.invoke(app, ["plan", "harden", bundle_name, "--no-interactive"])

        # Enforce SDD validation
        result = runner.invoke(app, ["enforce", "sdd", bundle_name, "--no-interactive"])

        # Should pass (default thresholds are low)
        assert result.exit_code == 0
        assert "Contracts/story" in result.stdout or "contracts" in result.stdout.lower()
        assert "Invariants/feature" in result.stdout or "invariants" in result.stdout.lower()
        assert "Architecture facets" in result.stdout or "architecture" in result.stdout.lower()

    def test_enforce_sdd_fails_without_sdd_manifest(self, tmp_path, monkeypatch):
        """Test enforce sdd fails gracefully when SDD manifest is missing."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        # Create a plan but don't harden it
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])

        # Try to enforce SDD validation
        result = runner.invoke(app, ["enforce", "sdd", bundle_name, "--no-interactive"])

        assert result.exit_code == 1
        assert "SDD manifest not found" in result.stdout or "SDD" in result.stdout
        assert "plan harden" in result.stdout or "harden" in result.stdout.lower()

    def test_enforce_sdd_fails_without_plan(self, tmp_path, monkeypatch):
        """Test enforce sdd fails gracefully when plan is missing."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "nonexistent-bundle"

        # Try to enforce SDD validation without creating bundle
        result = runner.invoke(app, ["enforce", "sdd", bundle_name, "--no-interactive"])

        assert result.exit_code == 1
        assert "not found" in result.stdout.lower() or "bundle" in result.stdout.lower()

    def test_enforce_sdd_with_custom_sdd_path(self, tmp_path, monkeypatch):
        """Test enforce sdd with custom SDD manifest path."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        # Create a plan and harden it to custom location
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        custom_sdd = tmp_path / "custom-sdd.yaml"
        runner.invoke(
            app,
            [
                "plan",
                "harden",
                bundle_name,
                "--no-interactive",
                "--sdd",
                str(custom_sdd),
            ],
        )

        # Enforce SDD validation with custom path
        result = runner.invoke(
            app,
            [
                "enforce",
                "sdd",
                bundle_name,
                "--no-interactive",
                "--sdd",
                str(custom_sdd),
            ],
        )

        assert result.exit_code == 0
        assert "SDD validation passed" in result.stdout or "validation" in result.stdout.lower()

    def test_enforce_sdd_with_custom_plan_path(self, tmp_path, monkeypatch):
        """Test enforce sdd with custom bundle name."""
        monkeypatch.chdir(tmp_path)

        # Create a plan bundle
        bundle_name = "custom-bundle"
        runner.invoke(
            app,
            [
                "plan",
                "init",
                bundle_name,
                "--no-interactive",
            ],
        )

        # Harden it
        runner.invoke(
            app,
            [
                "plan",
                "harden",
                bundle_name,
                "--no-interactive",
            ],
        )

        # Enforce SDD validation with bundle name
        result = runner.invoke(
            app,
            [
                "enforce",
                "sdd",
                bundle_name,
                "--no-interactive",
            ],
        )

        assert result.exit_code == 0
        assert "SDD validation passed" in result.stdout or "validation" in result.stdout.lower()

    def test_enforce_sdd_generates_markdown_report(self, tmp_path, monkeypatch):
        """Test enforce sdd generates markdown report."""
        monkeypatch.chdir(tmp_path)

        bundle_name = "test-bundle"
        # Create a plan and harden it
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        runner.invoke(app, ["plan", "harden", bundle_name, "--no-interactive"])

        # Enforce SDD validation with markdown format
        result = runner.invoke(
            app,
            [
                "enforce",
                "sdd",
                bundle_name,
                "--no-interactive",
                "--output-format",
                "markdown",
            ],
        )

        assert result.exit_code == 0

        # Verify markdown report was created
        from specfact_cli.utils.structure import SpecFactStructure

        reports_dir = SpecFactStructure.get_bundle_reports_dir(bundle_name, tmp_path) / "enforcement"
        report_files = list(reports_dir.glob("report-*.md"))
        assert len(report_files) > 0

        # Verify report content
        report_content = report_files[0].read_text()
        assert "# SDD Validation Report" in report_content or "SDD" in report_content
        assert "Summary" in report_content or "summary" in report_content.lower()

    def test_enforce_sdd_generates_json_report(self, tmp_path, monkeypatch):
        """Test enforce sdd generates JSON report."""
        monkeypatch.chdir(tmp_path)

        bundle_name = "test-bundle"
        # Create a plan and harden it
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        runner.invoke(app, ["plan", "harden", bundle_name, "--no-interactive"])

        # Enforce SDD validation with JSON format
        result = runner.invoke(
            app,
            [
                "enforce",
                "sdd",
                bundle_name,
                "--no-interactive",
                "--output-format",
                "json",
            ],
        )

        assert result.exit_code == 0

        # Verify JSON report was created
        from specfact_cli.utils.structure import SpecFactStructure

        reports_dir = SpecFactStructure.get_bundle_reports_dir(bundle_name, tmp_path) / "enforcement"
        report_files = list(reports_dir.glob("report-*.json"))
        assert len(report_files) > 0

        # Verify report is valid JSON
        import json

        report_data = json.loads(report_files[0].read_text())
        assert "deviations" in report_data
        assert "passed" in report_data

    def test_enforce_sdd_with_custom_output_path(self, tmp_path, monkeypatch):
        """Test enforce sdd with custom output path."""
        monkeypatch.chdir(tmp_path)
        bundle_name = "test-bundle"

        # Create a plan and harden it
        runner.invoke(app, ["plan", "init", bundle_name, "--no-interactive"])
        runner.invoke(app, ["plan", "harden", bundle_name, "--no-interactive"])

        # Enforce SDD validation with custom output
        custom_output = tmp_path / "custom-report.yaml"
        result = runner.invoke(
            app,
            [
                "enforce",
                "sdd",
                bundle_name,
                "--no-interactive",
                "--out",
                str(custom_output),
            ],
        )

        assert result.exit_code == 0
        assert custom_output.exists()

        # Verify report content
        from specfact_cli.utils.structured_io import load_structured_file

        report_data = load_structured_file(custom_output)
        assert "deviations" in report_data
        assert "passed" in report_data
