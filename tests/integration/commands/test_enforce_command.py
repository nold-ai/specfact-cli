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

        # Create a plan and harden it
        runner.invoke(app, ["plan", "init", "--no-interactive"])
        runner.invoke(app, ["plan", "harden", "--non-interactive"])

        # Enforce SDD validation
        result = runner.invoke(app, ["enforce", "sdd", "--non-interactive"])

        assert result.exit_code == 0
        assert "Hash match verified" in result.stdout
        assert "SDD validation passed" in result.stdout

        # Verify report was created
        reports_dir = tmp_path / ".specfact" / "reports" / "sdd"
        assert reports_dir.exists()
        report_files = list(reports_dir.glob("validation-*.yaml"))
        assert len(report_files) > 0

    def test_enforce_sdd_detects_hash_mismatch(self, tmp_path, monkeypatch):
        """Test enforce sdd detects hash mismatch."""
        monkeypatch.chdir(tmp_path)

        # Create a plan and harden it
        runner.invoke(app, ["plan", "init", "--no-interactive"])
        runner.invoke(app, ["plan", "harden", "--non-interactive"])

        # Modify the plan bundle hash in the SDD manifest directly to simulate a mismatch
        # This is more reliable than modifying the plan YAML, which might not change the hash
        sdd_path = tmp_path / ".specfact" / "sdd.yaml"
        from specfact_cli.utils.structured_io import StructuredFormat, dump_structured_file, load_structured_file

        sdd_data = load_structured_file(sdd_path)
        # Change the hash to a different value to simulate mismatch
        original_hash = sdd_data["plan_bundle_hash"]
        sdd_data["plan_bundle_hash"] = "different_hash_" + "x" * (len(original_hash) - len("different_hash_"))
        dump_structured_file(sdd_data, sdd_path, StructuredFormat.YAML)

        # Enforce SDD validation (should detect mismatch)
        result = runner.invoke(app, ["enforce", "sdd", "--non-interactive"])

        # Hash mismatch should be detected (HIGH severity deviation)
        assert result.exit_code == 1, "Hash mismatch should cause exit code 1"
        assert "Hash mismatch" in result.stdout or "✗" in result.stdout
        assert "SDD validation failed" in result.stdout

    def test_enforce_sdd_validates_coverage_thresholds(self, tmp_path, monkeypatch):
        """Test enforce sdd validates coverage thresholds."""
        monkeypatch.chdir(tmp_path)

        # Create a plan with features and stories
        runner.invoke(app, ["plan", "init", "--no-interactive"])
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
            ],
        )

        # Harden the plan
        runner.invoke(app, ["plan", "harden", "--non-interactive"])

        # Enforce SDD validation
        result = runner.invoke(app, ["enforce", "sdd", "--non-interactive"])

        # Should pass (default thresholds are low)
        assert result.exit_code == 0
        assert "Contracts/story" in result.stdout
        assert "Invariants/feature" in result.stdout
        assert "Architecture facets" in result.stdout

    def test_enforce_sdd_fails_without_sdd_manifest(self, tmp_path, monkeypatch):
        """Test enforce sdd fails gracefully when SDD manifest is missing."""
        monkeypatch.chdir(tmp_path)

        # Create a plan but don't harden it
        runner.invoke(app, ["plan", "init", "--no-interactive"])

        # Try to enforce SDD validation
        result = runner.invoke(app, ["enforce", "sdd", "--non-interactive"])

        assert result.exit_code == 1
        assert "SDD manifest not found" in result.stdout
        assert "plan harden" in result.stdout

    def test_enforce_sdd_fails_without_plan(self, tmp_path, monkeypatch):
        """Test enforce sdd fails gracefully when plan is missing."""
        monkeypatch.chdir(tmp_path)

        # Create SDD manifest without plan
        sdd_dir = tmp_path / ".specfact"
        sdd_dir.mkdir(parents=True, exist_ok=True)

        # Create a minimal SDD manifest
        from specfact_cli.models.sdd import (
            SDDCoverageThresholds,
            SDDEnforcementBudget,
            SDDHow,
            SDDManifest,
            SDDWhat,
            SDDWhy,
        )
        from specfact_cli.utils.structured_io import StructuredFormat, dump_structured_file

        sdd_manifest = SDDManifest(
            version="1.0.0",
            plan_bundle_id="test123456789012",
            plan_bundle_hash="test" * 16,
            promotion_status="draft",
            why=SDDWhy(intent="Test intent", target_users=None, value_hypothesis=None),
            what=SDDWhat(capabilities=["Test capability"]),
            how=SDDHow(architecture="Test architecture"),
            coverage_thresholds=SDDCoverageThresholds(
                contracts_per_story=1.0,
                invariants_per_feature=1.0,
                architecture_facets=3,
            ),
            enforcement_budget=SDDEnforcementBudget(
                shadow_budget_seconds=300,
                warn_budget_seconds=180,
                block_budget_seconds=90,
            ),
        )

        sdd_path = sdd_dir / "sdd.yaml"
        dump_structured_file(sdd_manifest.model_dump(mode="json"), sdd_path, StructuredFormat.YAML)

        # Try to enforce SDD validation
        result = runner.invoke(app, ["enforce", "sdd", "--non-interactive"])

        assert result.exit_code == 1
        assert "Plan bundle not found" in result.stdout

    def test_enforce_sdd_with_custom_sdd_path(self, tmp_path, monkeypatch):
        """Test enforce sdd with custom SDD manifest path."""
        monkeypatch.chdir(tmp_path)

        # Create a plan and harden it to custom location
        runner.invoke(app, ["plan", "init", "--no-interactive"])
        custom_sdd = tmp_path / "custom-sdd.yaml"
        runner.invoke(
            app,
            [
                "plan",
                "harden",
                "--non-interactive",
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
                "--non-interactive",
                "--sdd",
                str(custom_sdd),
            ],
        )

        assert result.exit_code == 0
        assert "SDD validation passed" in result.stdout

    def test_enforce_sdd_with_custom_plan_path(self, tmp_path, monkeypatch):
        """Test enforce sdd with custom plan bundle path."""
        monkeypatch.chdir(tmp_path)

        # Create a plan at custom location
        custom_plan = tmp_path / "custom-plan.yaml"
        runner.invoke(
            app,
            [
                "plan",
                "init",
                "--no-interactive",
                "--out",
                str(custom_plan),
            ],
        )

        # Harden it
        runner.invoke(
            app,
            [
                "plan",
                "harden",
                "--non-interactive",
                "--plan",
                str(custom_plan),
            ],
        )

        # Enforce SDD validation with custom plan path
        result = runner.invoke(
            app,
            [
                "enforce",
                "sdd",
                "--non-interactive",
                "--plan",
                str(custom_plan),
            ],
        )

        assert result.exit_code == 0
        assert "SDD validation passed" in result.stdout

    def test_enforce_sdd_generates_markdown_report(self, tmp_path, monkeypatch):
        """Test enforce sdd generates markdown report."""
        monkeypatch.chdir(tmp_path)

        # Create a plan and harden it
        runner.invoke(app, ["plan", "init", "--no-interactive"])
        runner.invoke(app, ["plan", "harden", "--non-interactive"])

        # Enforce SDD validation with markdown format
        result = runner.invoke(
            app,
            [
                "enforce",
                "sdd",
                "--non-interactive",
                "--format",
                "markdown",
            ],
        )

        assert result.exit_code == 0

        # Verify markdown report was created
        reports_dir = tmp_path / ".specfact" / "reports" / "sdd"
        report_files = list(reports_dir.glob("validation-*.md"))
        assert len(report_files) > 0

        # Verify report content
        report_content = report_files[0].read_text()
        assert "# SDD Validation Report" in report_content
        assert "Summary" in report_content

    def test_enforce_sdd_generates_json_report(self, tmp_path, monkeypatch):
        """Test enforce sdd generates JSON report."""
        monkeypatch.chdir(tmp_path)

        # Create a plan and harden it
        runner.invoke(app, ["plan", "init", "--no-interactive"])
        runner.invoke(app, ["plan", "harden", "--non-interactive"])

        # Enforce SDD validation with JSON format
        result = runner.invoke(
            app,
            [
                "enforce",
                "sdd",
                "--non-interactive",
                "--format",
                "json",
            ],
        )

        assert result.exit_code == 0

        # Verify JSON report was created
        reports_dir = tmp_path / ".specfact" / "reports" / "sdd"
        report_files = list(reports_dir.glob("validation-*.json"))
        assert len(report_files) > 0

        # Verify report is valid JSON
        import json

        report_data = json.loads(report_files[0].read_text())
        assert "deviations" in report_data
        assert "passed" in report_data

    def test_enforce_sdd_with_custom_output_path(self, tmp_path, monkeypatch):
        """Test enforce sdd with custom output path."""
        monkeypatch.chdir(tmp_path)

        # Create a plan and harden it
        runner.invoke(app, ["plan", "init", "--no-interactive"])
        runner.invoke(app, ["plan", "harden", "--non-interactive"])

        # Enforce SDD validation with custom output
        custom_output = tmp_path / "custom-report.yaml"
        result = runner.invoke(
            app,
            [
                "enforce",
                "sdd",
                "--non-interactive",
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
