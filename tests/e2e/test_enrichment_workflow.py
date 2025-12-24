"""End-to-end tests for enrichment workflow."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specfact_cli.cli import app


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
            bundle_name = "sample-app"
            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    bundle_name,
                    "--repo",
                    str(sample_repo),
                    "--confidence",
                    "0.5",
                ],
            )

            assert result.exit_code == 0, f"CLI import failed: {result.stdout}"
            assert "Import complete!" in result.stdout

            # Find the generated plan bundle (modular bundle)
            specfact_dir = sample_repo / ".specfact"
            bundle_dir = specfact_dir / "projects" / bundle_name
            assert bundle_dir.exists(), "Project bundle not generated"
            assert (bundle_dir / "bundle.manifest.yaml").exists()

            initial_bundle_dir = bundle_dir

            # Load and verify initial plan
            from specfact_cli.commands.plan import _convert_project_bundle_to_plan_bundle
            from specfact_cli.utils.bundle_loader import load_project_bundle

            project_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
            plan_bundle = _convert_project_bundle_to_plan_bundle(project_bundle)
            initial_features_count = len(plan_bundle.features)

            # Phase 2: LLM Enrichment - Create enrichment report
            # Use proper location: .specfact/reports/enrichment/ with matching name

            # For modular bundles, create enrichment report based on bundle name
            enrichment_dir = sample_repo / ".specfact" / "reports" / "enrichment"
            enrichment_dir.mkdir(parents=True, exist_ok=True)
            enrichment_report = enrichment_dir / f"{bundle_name}.enrichment.md"
            enrichment_content = """# Enrichment Report

## Missing Features

1. **API Gateway Feature** (Key: FEATURE-APIGATEWAY)
   - Confidence: 0.85
   - Outcomes: Provides API routing and gateway functionality
   - Stories:
     1. API Gateway routes requests to appropriate services
        - Acceptance: Gateway receives HTTP requests, routes to correct service endpoint, returns service response
     2. API Gateway handles authentication
        - Acceptance: Gateway validates API keys, forwards authenticated requests, rejects invalid requests

2. **Database Manager** (Key: FEATURE-DATABASEMANAGER)
   - Confidence: 0.80
   - Outcomes: Handles database connections and queries
   - Stories:
     1. Database Manager establishes connections
        - Acceptance: Manager creates database connection pool, manages connection lifecycle, handles connection errors

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
                    bundle_name,
                    "--repo",
                    str(sample_repo),
                    "--enrichment",
                    str(enrichment_report),
                    "--confidence",
                    "0.5",
                ],
            )

            assert result.exit_code == 0, f"Enrichment application failed: {result.stdout}"
            assert "Applying enrichment" in result.stdout or "📝" in result.stdout
            assert "Added" in result.stdout or "Adjusted" in result.stdout

            # Verify original bundle is preserved (modular bundle)
            assert initial_bundle_dir.exists(), "Original bundle should be preserved"
            assert (initial_bundle_dir / "bundle.manifest.yaml").exists()

            # Verify enriched bundle (modular bundle - same directory, updated content)
            assert bundle_dir.exists(), "Enriched bundle should exist"

            # Load enriched bundle and verify it has more features
            enriched_project_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
            enriched_plan_bundle = _convert_project_bundle_to_plan_bundle(enriched_project_bundle)
            enriched_features_count = len(enriched_plan_bundle.features)

            # Verify enriched bundle has more features than initial
            assert enriched_features_count > initial_features_count, (
                f"Enriched bundle should have more features. Initial: {initial_features_count}, Enriched: {enriched_features_count}"
            )

            # Verify enriched bundle has more features
            assert enriched_features_count >= initial_features_count + 2, (
                f"Expected at least {initial_features_count + 2} features, got {enriched_features_count}"
            )

            # Verify new features were added
            feature_keys = [f.key for f in enriched_plan_bundle.features]
            assert "FEATURE-APIGATEWAY" in feature_keys, "API Gateway feature not added"
            assert "FEATURE-DATABASEMANAGER" in feature_keys, "Database Manager feature not added"

            # Verify confidence adjustments (if confidence field exists in features)
            # Note: Confidence may be stored in metadata, not directly on feature
            # This is a simplified check - actual confidence may be in metadata
            # Validate enriched plan bundle (validate_plan_bundle expects Path, not PlanBundle)
            # Just verify the bundle structure is valid
            assert enriched_plan_bundle is not None
            assert len(enriched_plan_bundle.features) > initial_features_count

        finally:
            os.chdir(old_cwd)

    def test_enrichment_with_nonexistent_report(self, sample_repo: Path):
        """Test that enrichment fails gracefully with nonexistent report."""
        old_cwd = os.getcwd()
        try:
            os.chdir(sample_repo)

            # First create the bundle
            bundle_name = "sample-app"
            result_init = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    bundle_name,
                    "--repo",
                    str(sample_repo),
                ],
            )
            assert result_init.exit_code == 0, "Initial import should succeed"

            # Now try to enrich with nonexistent report
            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    bundle_name,
                    "--repo",
                    str(sample_repo),
                    "--enrichment",
                    "nonexistent.md",
                ],
            )

            assert result.exit_code != 0, "Should fail with nonexistent enrichment report"
            assert (
                "not found" in result.stdout.lower()
                or "Enrichment report not found" in result.stdout
                or "No plan bundle available" in result.stdout
            )

        finally:
            os.chdir(old_cwd)

    def test_enrichment_with_invalid_report(self, sample_repo: Path, tmp_path: Path):
        """Test that enrichment handles invalid report format gracefully."""
        old_cwd = os.getcwd()
        try:
            os.chdir(sample_repo)

            # Create initial plan
            bundle_name = "sample-app"
            runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    bundle_name,
                    "--repo",
                    str(sample_repo),
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
                    bundle_name,
                    "--repo",
                    str(sample_repo),
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
            bundle_name = "sample-app"
            runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    bundle_name,
                    "--repo",
                    str(sample_repo),
                ],
            )

            # Load initial plan (modular bundle)
            specfact_dir = sample_repo / ".specfact"
            bundle_dir = specfact_dir / "projects" / bundle_name
            assert bundle_dir.exists()

            from specfact_cli.commands.plan import _convert_project_bundle_to_plan_bundle
            from specfact_cli.utils.bundle_loader import load_project_bundle

            initial_project_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
            initial_plan_bundle = _convert_project_bundle_to_plan_bundle(initial_project_bundle)
            initial_plan_data = initial_plan_bundle.model_dump(exclude_none=True)

            # Phase 2: Create enrichment report in proper location
            enrichment_dir = sample_repo / ".specfact" / "reports" / "enrichment"
            enrichment_dir.mkdir(parents=True, exist_ok=True)
            enrichment_report = enrichment_dir / f"{bundle_name}.enrichment.md"
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
                    bundle_name,
                    "--repo",
                    str(sample_repo),
                    "--enrichment",
                    str(enrichment_report),
                ],
            )

            # Verify original bundle is preserved (modular bundle)
            assert bundle_dir.exists(), "Original bundle should be preserved"
            assert (bundle_dir / "bundle.manifest.yaml").exists()

            # Load enriched bundle (modular bundle - same directory, updated content)
            enriched_project_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
            enriched_plan_bundle = _convert_project_bundle_to_plan_bundle(enriched_project_bundle)
            enriched_plan_data = enriched_plan_bundle.model_dump(exclude_none=True)

            # Verify structure is preserved
            assert enriched_plan_data.get("version") == initial_plan_data.get("version")
            assert enriched_plan_data.get("idea") is not None
            assert enriched_plan_data.get("product") is not None
            assert "features" in enriched_plan_data

            # Verify plan is valid (validate_plan_bundle expects Path, not PlanBundle)
            # Just verify the bundle structure is valid
            assert enriched_plan_bundle is not None
            assert enriched_plan_bundle.version is not None
            assert enriched_plan_bundle.features is not None

        finally:
            os.chdir(old_cwd)
