"""E2E tests for complete enforcement workflow."""

import os

from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.utils.yaml_utils import dump_yaml


runner = CliRunner()


class TestEnforcementWorkflow:
    """Test suite for complete enforcement workflow."""

    def test_complete_enforcement_workflow_with_blocking(self, tmp_path):
        """
        Test complete workflow: init → enforce → compare with blocking.

        This tests:
        1. Create manual plan with a feature
        2. Create auto plan missing that feature (HIGH severity deviation)
        3. Set enforcement to balanced mode (blocks HIGH)
        4. Compare plans with enforcement enabled
        5. Verify HIGH severity deviations block execution
        """
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Step 1: Create manual plan with required feature
            manual_plan = {
                "version": "1.0",
                "product": {
                    "key": "TEST",
                    "title": "Test Product",
                },
                "features": [
                    {
                        "key": "FEATURE-001",
                        "title": "User Authentication",
                        "outcome": "Users can securely authenticate",
                        "priority": "HIGH",
                        "stories": [
                            {
                                "key": "STORY-001",
                                "title": "As a user I want to login",
                                "acceptance": ["Valid credentials accepted"],
                            }
                        ],
                    }
                ],
            }

            plans_dir = tmp_path / ".specfact" / "plans"
            plans_dir.mkdir(parents=True, exist_ok=True)
            dump_yaml(manual_plan, plans_dir / "main.bundle.yaml")

            # Step 2: Create auto plan missing the feature (causes HIGH deviation)
            auto_plan = {
                "version": "1.0",
                "product": {
                    "key": "TEST",
                    "title": "Test Product",
                },
                "features": [],  # Missing FEATURE-001 creates HIGH severity deviation
            }

            plans_dir = tmp_path / ".specfact" / "plans"
            plans_dir.mkdir(parents=True, exist_ok=True)
            dump_yaml(auto_plan, plans_dir / "auto-derived.2025-01-01T00-00-00.bundle.yaml")

            # Step 3: Set enforcement to balanced mode (blocks HIGH)
            result = runner.invoke(
                app,
                ["enforce", "stage", "--preset", "balanced"],
            )
            assert result.exit_code == 0
            assert "Enforcement mode set to balanced" in result.stdout

            # Step 4: Compare plans with enforcement enabled (use explicit paths)
            manual_plan_file = plans_dir / "main.bundle.yaml"
            auto_plan_file = plans_dir / "auto-derived.2025-01-01T00-00-00.bundle.yaml"
            result = runner.invoke(
                app,
                [
                    "plan",
                    "compare",
                    "--manual",
                    str(manual_plan_file),
                    "--auto",
                    str(auto_plan_file),
                ],
            )

            # Should fail because there is a HIGH severity deviation (missing feature)
            assert result.exit_code == 1
            assert "Enforcement BLOCKED" in result.stdout or "deviation(s) violate quality gates" in result.stdout

        finally:
            os.chdir(old_cwd)

    def test_enforcement_workflow_with_minimal_preset(self, tmp_path):
        """
        Test enforcement workflow with minimal preset (no blocking).

        This tests:
        1. Create plans with HIGH deviation
        2. Set enforcement to minimal mode (never blocks)
        3. Verify execution succeeds even with HIGH deviations
        """
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Step 1: Create manual plan with feature
            manual_plan = {
                "version": "1.0",
                "product": {
                    "key": "TEST",
                    "title": "Test Product",
                },
                "features": [
                    {
                        "key": "FEATURE-001",
                        "title": "Payment Processing",
                        "outcome": "Process payments",
                        "priority": "HIGH",
                        "stories": [],
                    }
                ],
            }

            plans_dir = tmp_path / ".specfact" / "plans"
            plans_dir.mkdir(parents=True, exist_ok=True)
            dump_yaml(manual_plan, plans_dir / "main.bundle.yaml")

            # Step 2: Create auto plan missing the feature
            auto_plan = {
                "version": "1.0",
                "product": {
                    "key": "TEST",
                    "title": "Test Product",
                },
                "features": [],  # Missing feature creates HIGH deviation
            }

            plans_dir = tmp_path / ".specfact" / "plans"
            plans_dir.mkdir(parents=True, exist_ok=True)
            dump_yaml(auto_plan, plans_dir / "auto-derived.2025-01-01T00-00-00.bundle.yaml")

            # Step 3: Set enforcement to minimal (never blocks)
            result = runner.invoke(
                app,
                ["enforce", "stage", "--preset", "minimal"],
            )
            assert result.exit_code == 0

            # Step 4: Compare plans with enforcement enabled (use explicit paths)
            manual_plan_file = plans_dir / "main.bundle.yaml"
            auto_plan_file = plans_dir / "auto-derived.2025-01-01T00-00-00.bundle.yaml"
            result = runner.invoke(
                app,
                [
                    "plan",
                    "compare",
                    "--manual",
                    str(manual_plan_file),
                    "--auto",
                    str(auto_plan_file),
                ],
            )

            # Should succeed because minimal preset never blocks
            assert result.exit_code == 0
            assert "Enforcement PASSED" in result.stdout

        finally:
            os.chdir(old_cwd)

    def test_enforcement_workflow_without_config(self, tmp_path):
        """
        Test workflow without enforcement config (default behavior).

        This tests:
        1. Compare plans without enforcement config
        2. Verify deviations don't block execution
        3. Verify exit code is 0 even with deviations
        """
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Step 1: Create manual plan
            manual_plan = {
                "version": "1.0",
                "product": {
                    "key": "TEST",
                    "title": "Test Product",
                },
                "features": [
                    {
                        "key": "FEATURE-001",
                        "title": "Data Export",
                        "outcome": "Export data",
                        "priority": "MEDIUM",
                        "stories": [],
                    }
                ],
            }

            plans_dir = tmp_path / ".specfact" / "plans"
            plans_dir.mkdir(parents=True, exist_ok=True)
            dump_yaml(manual_plan, plans_dir / "main.bundle.yaml")

            # Step 2: Create different code
            code_file = tmp_path / "reporting.py"
            code_file.write_text(
                '''"""Reporting module."""

class ReportGenerator:
    def generate_report(self):
        pass
'''
            )

            # Step 3: Run brownfield analysis (no enforcement config set)
            result = runner.invoke(
                app,
                ["import", "from-code", "auto-derived", "--repo", str(tmp_path), "--confidence", "0.5"],
            )
            assert result.exit_code == 0

            # Step 4: Compare plans without enforcement config (create temporary PlanBundle files)
            from specfact_cli.commands.plan import _convert_project_bundle_to_plan_bundle
            from specfact_cli.generators.plan_generator import PlanGenerator
            from specfact_cli.models.plan import PlanBundle
            from specfact_cli.utils.bundle_loader import load_project_bundle

            plans_dir = tmp_path / ".specfact" / "plans"
            plans_dir.mkdir(parents=True, exist_ok=True)

            # Load manual plan
            manual_plan_path = plans_dir / "main.bundle.yaml"
            if not manual_plan_path.exists():
                dump_yaml(manual_plan, manual_plan_path)
            # Load from file
            from specfact_cli.utils.yaml_utils import load_yaml

            manual_plan_dict = load_yaml(manual_plan_path)
            manual_plan_bundle = PlanBundle.model_validate(manual_plan_dict)

            # Load auto-derived bundle and convert to PlanBundle
            auto_bundle_dir = tmp_path / ".specfact" / "projects" / "auto-derived"
            auto_project_bundle = load_project_bundle(auto_bundle_dir, validate_hashes=False)
            auto_plan_bundle = _convert_project_bundle_to_plan_bundle(auto_project_bundle)

            # Generate temporary files for comparison
            manual_plan_file = plans_dir / "main.bundle.yaml"
            auto_plan_file = plans_dir / "auto-derived.bundle.yaml"

            generator = PlanGenerator()
            generator.generate(manual_plan_bundle, manual_plan_file)
            generator.generate(auto_plan_bundle, auto_plan_file)

            result = runner.invoke(
                app,
                [
                    "plan",
                    "compare",
                    "--manual",
                    str(manual_plan_file),
                    "--auto",
                    str(auto_plan_file),
                ],
            )

            # Should succeed (no enforcement config means no blocking)
            assert result.exit_code == 0
            # Should not show enforcement section
            assert "Enforcement Rules" not in result.stdout

        finally:
            os.chdir(old_cwd)

    def test_enforcement_displays_actions(self, tmp_path):
        """
        Test that enforcement displays actions for each deviation.

        This tests:
        1. Create plans with deviations
        2. Set enforcement config
        3. Verify enforcement actions are displayed
        """
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Create manual and auto plan files (legacy layout) to drive comparison
            plans_dir = tmp_path / ".specfact" / "plans"
            plans_dir.mkdir(parents=True, exist_ok=True)

            manual_plan = {
                "version": "1.0",
                "product": {
                    "key": "TEST",
                    "title": "Test Product",
                },
                "features": [
                    {
                        "key": "FEATURE-001",
                        "title": "Test Feature",
                        "outcome": "Test outcome",
                        "priority": "MEDIUM",
                        "stories": [],
                    }
                ],
            }

            auto_plan = {
                "version": "1.0",
                "product": {
                    "key": "TEST",
                    "title": "Test Product",
                },
                "features": [],
            }

            manual_plan_path = plans_dir / "manual.bundle.yaml"
            auto_plan_path = plans_dir / "auto-derived.bundle.yaml"
            dump_yaml(manual_plan, manual_plan_path)
            dump_yaml(auto_plan, auto_plan_path)

            # Step 2: Set enforcement to balanced
            result = runner.invoke(
                app,
                ["enforce", "stage", "--preset", "balanced"],
            )
            assert result.exit_code == 0

            # Step 3: Compare plans
            result = runner.invoke(
                app,
                ["plan", "compare", "--manual", str(manual_plan_path), "--auto", str(auto_plan_path)],
            )

            # Verify enforcement section is displayed when deviations exist
            assert result.exit_code == 0
            assert "Comparison Results" in result.stdout
            assert "Enforcement Rules" in result.stdout

        finally:
            os.chdir(old_cwd)
