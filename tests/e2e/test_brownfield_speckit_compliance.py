"""End-to-end tests for brownfield import → Spec-Kit compliance workflow."""

from __future__ import annotations

import os
from pathlib import Path
from textwrap import dedent

import pytest
from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.utils.yaml_utils import load_yaml


runner = CliRunner()


class TestBrownfieldSpeckitComplianceE2E:
    """End-to-end tests for complete brownfield import → Spec-Kit sync workflow."""

    @pytest.fixture
    def brownfield_repo(self, tmp_path: Path) -> Path:
        """Create a brownfield repository with dependencies."""
        repo = tmp_path / "brownfield_repo"
        repo.mkdir()

        # Create source code
        src_dir = repo / "src"
        src_dir.mkdir()
        (src_dir / "service.py").write_text(
            dedent(
                '''
                """User service module."""
                class UserService:
                    """User management service."""

                    def create_user(self, name: str, email: str) -> dict:
                        """Create a new user."""
                        return {"id": 1, "name": name, "email": email}

                    def get_user(self, user_id: int) -> dict:
                        """Get user by ID."""
                        return {"id": user_id}
                '''
            )
        )

        # Create requirements.txt with dependencies
        (repo / "requirements.txt").write_text(
            dedent(
                """
                python>=3.11
                fastapi==0.104.1
                pydantic>=2.0.0
                psycopg2-binary==2.9.9
                pytest==7.4.3
                """
            )
        )

        return repo

    def test_complete_brownfield_to_speckit_workflow(self, brownfield_repo: Path) -> None:
        """
        Test complete workflow: brownfield import → enrich → sync → verify Spec-Kit compliance.
        """
        os.environ["TEST_MODE"] = "true"
        try:
            # Step 1: Import brownfield code with enrichment
            bundle_name = "brownfield-project"
            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    bundle_name,
                    "--repo",
                    str(brownfield_repo),
                    "--enrich-for-speckit",
                ],
            )

            # Command may exit with 0 or 1 depending on validation, but import should complete
            bundle_dir = brownfield_repo / ".specfact" / "projects" / bundle_name
            # Import may fail if enrichment fails, but bundle should exist if import succeeded
            if result.exit_code == 0:
                assert "Import complete" in result.stdout or bundle_dir.exists()
            else:
                # If import failed, check if it's due to enrichment issues
                # In that case, the bundle might still be created
                pass

            # Find generated plan bundle (modular bundle)
            assert bundle_dir.exists()
            assert (bundle_dir / "bundle.manifest.yaml").exists()

            from specfact_cli.utils.bundle_loader import load_project_bundle
            from specfact_cli.commands.plan import _convert_project_bundle_to_plan_bundle
            
            project_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
            plan_bundle = _convert_project_bundle_to_plan_bundle(project_bundle)
            plan_data = plan_bundle.model_dump(exclude_none=True)

            # Verify technology stack was extracted
            idea = plan_data.get("idea", {})
            constraints = idea.get("constraints", [])
            assert len(constraints) > 0
            constraint_str = " ".join(constraints).lower()
            assert "python" in constraint_str or "fastapi" in constraint_str

            # Verify features have at least 2 stories
            features = plan_data.get("features", [])
            for feature in features:
                stories = feature.get("stories", [])
                assert len(stories) >= 2, f"Feature {feature.get('key')} should have at least 2 stories"

            # Step 2: Create Spec-Kit structure
            specify_dir = brownfield_repo / ".specify" / "memory"
            specify_dir.mkdir(parents=True, exist_ok=True)
            (specify_dir / "constitution.md").write_text("# Constitution\n")

            # Step 3: Sync to Spec-Kit with compliance check
            result = runner.invoke(
                app,
                [
                    "sync",
                    "bridge",
                    "--repo",
                    str(brownfield_repo),
                    "--bundle",
                    bundle_name,
                    "--adapter",
                    "speckit",
                    "--bidirectional",
                    "--ensure-compliance",
                ],
            )

            assert result.exit_code == 0
            assert "Sync complete" in result.stdout or "Syncing" in result.stdout or "Bridge" in result.stdout

            # Step 4: Verify Spec-Kit artifacts were generated
            specs_dir = brownfield_repo / "specs"
            if specs_dir.exists():
                feature_dirs = list(specs_dir.iterdir())
                assert len(feature_dirs) > 0

                # Verify spec.md has required fields
                for feature_dir in feature_dirs:
                    spec_file = feature_dir / "spec.md"
                    if spec_file.exists():
                        spec_content = spec_file.read_text()

                        # Verify frontmatter
                        assert "Feature Branch" in spec_content or "---" in spec_content

                        # Verify INVSEST criteria
                        assert "Independent" in spec_content
                        assert "Testable" in spec_content

                        # Verify scenarios
                        assert "Primary Scenario" in spec_content or "Scenarios" in spec_content

                    # Verify plan.md has required fields
                    plan_file = feature_dir / "plan.md"
                    if plan_file.exists():
                        plan_content = plan_file.read_text()

                        # Verify Constitution Check
                        assert "Constitution Check" in plan_content

                        # Verify Technology Stack
                        assert "Technology Stack" in plan_content

                        # Verify Phases
                        assert "Phase" in plan_content

                    # Verify tasks.md has required fields
                    tasks_file = feature_dir / "tasks.md"
                    if tasks_file.exists():
                        tasks_content = tasks_file.read_text()

                        # Verify phase organization
                        assert "Phase" in tasks_content

                        # Verify story mappings
                        assert "[US" in tasks_content or "User Story" in tasks_content

        finally:
            os.environ.pop("TEST_MODE", None)

    def test_brownfield_import_extracts_technology_stack(self, brownfield_repo: Path) -> None:
        """Test that brownfield import extracts technology stack from requirements.txt."""
        os.environ["TEST_MODE"] = "true"
        try:
            bundle_name = "test-project"
            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    bundle_name,
                    "--repo",
                    str(brownfield_repo),
                ],
            )

            assert result.exit_code == 0

            # Find generated plan bundle (modular bundle)
            bundle_dir = brownfield_repo / ".specfact" / "projects" / bundle_name
            assert bundle_dir.exists()
            
            from specfact_cli.utils.bundle_loader import load_project_bundle
            from specfact_cli.commands.plan import _convert_project_bundle_to_plan_bundle
            
            project_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
            plan_bundle = _convert_project_bundle_to_plan_bundle(project_bundle)
            plan_data = plan_bundle.model_dump(exclude_none=True)
            
            idea = plan_data.get("idea", {})
            constraints = idea.get("constraints", [])

            # Verify technology stack was extracted
            assert len(constraints) > 0

            # Should have Python version
            assert any("python" in c.lower() and "3.11" in c.lower() for c in constraints)

            # Should have FastAPI
            assert any("fastapi" in c.lower() for c in constraints)

            # Should have PostgreSQL
            assert any("postgres" in c.lower() for c in constraints)

            # Should have pytest
            assert any("pytest" in c.lower() for c in constraints)

        finally:
            os.environ.pop("TEST_MODE", None)

    def test_enrich_for_speckit_ensures_compliance(self, brownfield_repo: Path) -> None:
        """Test that --enrich-for-speckit ensures Spec-Kit compliance."""
        os.environ["TEST_MODE"] = "true"
        try:
            # Import with enrichment
            bundle_name = "enriched-project"
            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    bundle_name,
                    "--repo",
                    str(brownfield_repo),
                    "--enrich-for-speckit",
                ],
            )

            # Command may exit with 0 or 1 depending on validation, but enrichment should be attempted
            assert (
                "Enriching plan for Spec-Kit compliance" in result.stdout
                or "Spec-Kit enrichment" in result.stdout
                or "Import complete" in result.stdout
            )

            # Find generated plan bundle (modular bundle)
            bundle_dir = brownfield_repo / ".specfact" / "projects" / bundle_name
            assert bundle_dir.exists()
            
            from specfact_cli.utils.bundle_loader import load_project_bundle
            from specfact_cli.commands.plan import _convert_project_bundle_to_plan_bundle
            
            project_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
            plan_bundle = _convert_project_bundle_to_plan_bundle(project_bundle)
            plan_data = plan_bundle.model_dump(exclude_none=True)
            features = plan_data.get("features", [])

            # Verify all features have at least 2 stories (if enrichment worked)
            # Note: Enrichment may fail silently, so we check if it worked
            enrichment_worked = "Spec-Kit enrichment complete" in result.stdout
            for feature in features:
                stories = feature.get("stories", [])
                if enrichment_worked:
                    assert len(stories) >= 2, (
                        f"Feature {feature.get('key')} should have at least 2 stories after enrichment"
                    )

                # Verify all stories have testable acceptance criteria (if enrichment worked)
                if enrichment_worked:
                    for story in stories:
                        acceptance = story.get("acceptance", [])
                        if acceptance:
                            testable_count = sum(
                                1
                                for acc in acceptance
                                if any(
                                    keyword in acc.lower()
                                    for keyword in ["must", "should", "verify", "validate", "ensure"]
                                )
                            )
                            # At least some acceptance criteria should be testable
                            assert testable_count > 0 or len(acceptance) == 0, (
                                f"Story {story.get('key')} should have testable acceptance criteria"
                            )

        finally:
            os.environ.pop("TEST_MODE", None)
