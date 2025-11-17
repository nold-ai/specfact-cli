"""End-to-end tests for enrichment workflow."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.utils.yaml_utils import load_yaml
from specfact_cli.validators.schema import validate_plan_bundle


runner = CliRunner()


class TestEnrichmentWorkflow:
    """Test complete enrichment workflow end-to-end."""

    @pytest.fixture
    def sample_repo(self, tmp_path: Path) -> Path:
        """Create a sample repository with Python code."""
        repo = tmp_path / "sample_repo"
        repo.mkdir()

        # Create a simple Python module
        src_dir = repo / "src"
        src_dir.mkdir()
        (src_dir / "app.py").write_text(
            '''"""
Sample application module.
"""

class UserManager:
    """Manages user operations."""

    def create_user(self, name: str) -> bool:
        """Create a new user."""
        return True

    def delete_user(self, user_id: int) -> bool:
        """Delete a user."""
        return True


class AuthService:
    """Handles authentication."""

    def login(self, username: str, password: str) -> bool:
        """Authenticate user."""
        return True
'''
        )

        return repo

    def test_dual_stack_enrichment_workflow(self, sample_repo: Path, tmp_path: Path):
        """
        Test complete dual-stack enrichment workflow:
        1. Phase 1: CLI Grounding - Run import from-code
        2. Phase 2: LLM Enrichment - Generate enrichment report
        3. Phase 3: CLI Artifact Creation - Apply enrichment via CLI
        """
        old_cwd = os.getcwd()
        try:
            os.chdir(sample_repo)

            # Phase 1: CLI Grounding - Run initial import
            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    "--repo",
                    str(sample_repo),
                    "--name",
                    "Sample App",
                    "--confidence",
                    "0.5",
                ],
            )

            assert result.exit_code == 0, f"CLI import failed: {result.stdout}"
            assert "Import complete!" in result.stdout

            # Find the generated plan bundle
            specfact_dir = sample_repo / ".specfact"
            plans_dir = specfact_dir / "plans"
            plan_files = list(plans_dir.glob("sample-app*.bundle.yaml"))
            assert len(plan_files) > 0, "Plan bundle not generated"

            initial_plan_path = plan_files[0]

            # Load and verify initial plan
            initial_plan_data = load_yaml(initial_plan_path)
            initial_features_count = len(initial_plan_data.get("features", []))

            # Phase 2: LLM Enrichment - Create enrichment report
            # Use proper location: .specfact/reports/enrichment/ with matching name
            from specfact_cli.utils.structure import SpecFactStructure

            enrichment_report = SpecFactStructure.get_enrichment_report_path(initial_plan_path, base_path=sample_repo)
            enrichment_content = """# Enrichment Report

## Missing Features

1. **API Gateway Feature** (Key: FEATURE-APIGATEWAY)
   - Confidence: 0.85
   - Outcomes: Provides API routing and gateway functionality
   - Reason: AST missed because it's in a separate service module

2. **Database Manager** (Key: FEATURE-DATABASEMANAGER)
   - Confidence: 0.80
   - Outcomes: Handles database connections and queries
   - Reason: Not detected in AST analysis

## Confidence Adjustments

- FEATURE-USERMANAGER → 0.95 (strong test coverage and documentation)
- FEATURE-AUTHSERVICE → 0.90 (well-implemented authentication logic)

## Business Context

- Priority: "Core application for user management"
- Constraint: "Must support both REST and GraphQL APIs"
- Unknown: "Future microservices migration requirements"
"""
            enrichment_report.write_text(enrichment_content)

            # Phase 3: CLI Artifact Creation - Apply enrichment
            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    "--repo",
                    str(sample_repo),
                    "--name",
                    "Sample App",
                    "--enrichment",
                    str(enrichment_report),
                    "--confidence",
                    "0.5",
                ],
            )

            assert result.exit_code == 0, f"Enrichment application failed: {result.stdout}"
            assert "Applying enrichment" in result.stdout or "📝" in result.stdout
            assert "Added" in result.stdout or "Adjusted" in result.stdout

            # Verify original plan is preserved
            assert initial_plan_path.exists(), "Original plan should be preserved"
            assert initial_plan_path in plan_files, "Original plan should still exist"

            # Verify enriched plan bundle with new naming convention
            plan_files_after = list(plans_dir.glob("sample-app*.bundle.yaml"))
            assert len(plan_files_after) > 0, "Enriched plan bundle not generated"

            # Find enriched plan (should have .enriched. in filename)
            enriched_plans = [p for p in plan_files_after if ".enriched." in p.name]
            assert len(enriched_plans) > 0, f"Enriched plan not found. Files: {[p.name for p in plan_files_after]}"
            enriched_plan_path = enriched_plans[0]

            # Verify enriched plan naming convention: <name>.<original-timestamp>.enriched.<enrichment-timestamp>.bundle.yaml
            assert ".enriched." in enriched_plan_path.name, (
                f"Enriched plan should have .enriched. in name: {enriched_plan_path.name}"
            )
            assert enriched_plan_path.name.startswith("sample-app"), "Enriched plan should start with plan name"
            assert enriched_plan_path.name.endswith(".bundle.yaml"), "Enriched plan should end with .bundle.yaml"

            # Verify original plan is different from enriched plan
            assert enriched_plan_path != initial_plan_path, "Enriched plan should be different from original"

            # Load and verify enriched plan
            enriched_plan_data = load_yaml(enriched_plan_path)
            enriched_features = enriched_plan_data.get("features", [])

            # Should have more features (original + 2 new ones)
            assert len(enriched_features) >= initial_features_count + 2, (
                f"Expected at least {initial_features_count + 2} features, got {len(enriched_features)}"
            )

            # Verify new features were added
            feature_keys = [f.get("key") for f in enriched_features]
            assert "FEATURE-APIGATEWAY" in feature_keys, "API Gateway feature not added"
            assert "FEATURE-DATABASEMANAGER" in feature_keys, "Database Manager feature not added"

            # Verify confidence adjustments
            for feature in enriched_features:
                if feature.get("key") == "FEATURE-USERMANAGER":
                    assert feature.get("confidence") == 0.95, "Confidence not adjusted for UserManager"
                elif feature.get("key") == "FEATURE-AUTHSERVICE":
                    assert feature.get("confidence") == 0.90, "Confidence not adjusted for AuthService"

            # Validate enriched plan bundle
            is_valid, error, bundle = validate_plan_bundle(enriched_plan_path)
            assert is_valid, f"Enriched plan bundle validation failed: {error}"
            assert bundle is not None, "Enriched plan bundle not loaded"

        finally:
            os.chdir(old_cwd)

    def test_enrichment_with_nonexistent_report(self, sample_repo: Path):
        """Test that enrichment fails gracefully with nonexistent report."""
        old_cwd = os.getcwd()
        try:
            os.chdir(sample_repo)

            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    "--repo",
                    str(sample_repo),
                    "--name",
                    "Sample App",
                    "--enrichment",
                    "nonexistent.md",
                ],
            )

            assert result.exit_code != 0, "Should fail with nonexistent enrichment report"
            assert "not found" in result.stdout.lower() or "Enrichment report not found" in result.stdout

        finally:
            os.chdir(old_cwd)

    def test_enrichment_with_invalid_report(self, sample_repo: Path, tmp_path: Path):
        """Test that enrichment handles invalid report format gracefully."""
        old_cwd = os.getcwd()
        try:
            os.chdir(sample_repo)

            # Create initial plan
            runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    "--repo",
                    str(sample_repo),
                    "--name",
                    "Sample App",
                ],
            )

            # Create invalid enrichment report (empty file)
            invalid_report = tmp_path / "invalid.md"
            invalid_report.write_text("")

            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    "--repo",
                    str(sample_repo),
                    "--name",
                    "Sample App",
                    "--enrichment",
                    str(invalid_report),
                ],
            )

            # Should either succeed (empty enrichment) or fail gracefully
            # Empty enrichment is valid (no changes)
            assert result.exit_code in [0, 1], "Should handle invalid report gracefully"

        finally:
            os.chdir(old_cwd)

    def test_enrichment_preserves_plan_structure(self, sample_repo: Path, tmp_path: Path):
        """Test that enrichment preserves plan bundle structure."""
        old_cwd = os.getcwd()
        try:
            os.chdir(sample_repo)

            # Phase 1: Initial import
            runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    "--repo",
                    str(sample_repo),
                    "--name",
                    "Sample App",
                ],
            )

            # Load initial plan
            specfact_dir = sample_repo / ".specfact"
            plans_dir = specfact_dir / "plans"
            initial_plan_path = next(iter(plans_dir.glob("sample-app*.bundle.yaml")))
            initial_plan_data = load_yaml(initial_plan_path)

            # Phase 2: Create enrichment report in proper location
            from specfact_cli.utils.structure import SpecFactStructure

            enrichment_report = SpecFactStructure.get_enrichment_report_path(initial_plan_path, base_path=sample_repo)
            enrichment_report.write_text(
                """# Enrichment Report

## Confidence Adjustments

- FEATURE-USERMANAGER → 0.95
"""
            )

            # Phase 3: Apply enrichment
            runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    "--repo",
                    str(sample_repo),
                    "--name",
                    "Sample App",
                    "--enrichment",
                    str(enrichment_report),
                ],
            )

            # Verify original plan is preserved
            assert initial_plan_path.exists(), "Original plan should be preserved"

            # Find enriched plan (should have .enriched. in filename)
            plan_files_after = list(plans_dir.glob("sample-app*.bundle.yaml"))
            enriched_plans = [p for p in plan_files_after if ".enriched." in p.name]
            assert len(enriched_plans) > 0, f"Enriched plan not found. Files: {[p.name for p in plan_files_after]}"
            enriched_plan_path = enriched_plans[0]

            # Verify enriched plan naming convention
            assert ".enriched." in enriched_plan_path.name, (
                f"Enriched plan should have .enriched. in name: {enriched_plan_path.name}"
            )
            assert enriched_plan_path != initial_plan_path, "Enriched plan should be different from original"

            # Load enriched plan
            enriched_plan_data = load_yaml(enriched_plan_path)

            # Verify structure is preserved
            assert enriched_plan_data.get("version") == initial_plan_data.get("version")
            assert enriched_plan_data.get("idea") is not None
            assert enriched_plan_data.get("product") is not None
            assert "features" in enriched_plan_data

            # Verify plan is valid
            is_valid, error, _ = validate_plan_bundle(enriched_plan_path)
            assert is_valid, f"Enriched plan structure invalid: {error}"

        finally:
            os.chdir(old_cwd)
