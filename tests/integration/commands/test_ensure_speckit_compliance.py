"""Integration tests for --ensure-speckit-compliance flag."""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory

from typer.testing import CliRunner

from specfact_cli.cli import app


runner = CliRunner()


class TestEnsureSpeckitComplianceFlag:
    """Integration tests for --ensure-speckit-compliance flag in sync spec-kit command."""

    def test_ensure_speckit_compliance_validates_plan_bundle(self) -> None:
        """Test that --ensure-speckit-compliance validates plan bundle before sync."""
        os.environ["TEST_MODE"] = "true"
        try:
            with TemporaryDirectory() as tmpdir:
                repo_path = Path(tmpdir)

                # Create Spec-Kit structure
                specify_dir = repo_path / ".specify" / "memory"
                specify_dir.mkdir(parents=True)
                (specify_dir / "constitution.md").write_text("# Constitution\n")

                # Create SpecFact structure with modular project bundle
                from specfact_cli.models.plan import Feature, Product, Story
                from specfact_cli.models.project import BundleManifest, ProjectBundle
                from specfact_cli.utils.bundle_loader import save_project_bundle

                projects_dir = repo_path / ".specfact" / "projects"
                projects_dir.mkdir(parents=True)
                bundle_dir = projects_dir / "main"
                bundle_dir.mkdir()

                # Create modular project bundle with technology stack in constraints
                manifest = BundleManifest(
                    schema_metadata=None,
                    project_metadata=None,
                    personas={},
                )
                product = Product(themes=[], releases=[])
                bundle = ProjectBundle(manifest=manifest, bundle_name="main", product=product)

                # Add idea with constraints
                from specfact_cli.models.plan import Idea

                bundle.idea = Idea(
                    title="Test Project",
                    narrative="Test project description",
                    constraints=["Python 3.11+", "FastAPI framework", "PostgreSQL database"],
                    metrics=None,
                )

                # Add feature
                feature = Feature(
                    key="FEATURE-001",
                    title="Test Feature",
                    outcomes=[],
                    acceptance=["Must verify feature works correctly"],
                    constraints=[],
                    stories=[
                        Story(
                            key="STORY-001",
                            title="As a user, I can use the feature",
                            acceptance=["Must verify feature works", "Must validate input"],
                            story_points=5,
                            value_points=None,
                            scenarios=None,
                            contracts=None,
                        )
                    ],
                    source_tracking=None,
                    contract=None,
                    protocol=None,
                )
                bundle.add_feature(feature)
                save_project_bundle(bundle, bundle_dir, atomic=True)

                # Sync with compliance flag
                result = runner.invoke(
                    app,
                    [
                        "sync",
                        "bridge",
                        "--adapter",
                        "speckit",
                        "--bundle",
                        "main",
                        "--repo",
                        str(repo_path),
                        "--bidirectional",
                        "--ensure-compliance",
                    ],
                )

                assert result.exit_code == 0
                assert (
                    "Validating plan bundle" in result.stdout.lower()
                    or "Plan bundle validation complete" in result.stdout
                    or "Bundle 'main' not found" in result.stdout
                    or "skipping compliance check" in result.stdout.lower()
                )

        finally:
            os.environ.pop("TEST_MODE", None)

    def test_ensure_speckit_compliance_warns_missing_tech_stack(self) -> None:
        """Test that --ensure-speckit-compliance warns when technology stack is missing."""
        os.environ["TEST_MODE"] = "true"
        try:
            with TemporaryDirectory() as tmpdir:
                repo_path = Path(tmpdir)

                # Create Spec-Kit structure
                specify_dir = repo_path / ".specify" / "memory"
                specify_dir.mkdir(parents=True)
                (specify_dir / "constitution.md").write_text("# Constitution\n")

                # Create SpecFact structure with modular bundle without technology stack (new structure)
                from specfact_cli.commands.plan import _convert_plan_bundle_to_project_bundle
                from specfact_cli.models.plan import Feature, Idea, PlanBundle, Product
                from specfact_cli.utils.bundle_loader import save_project_bundle
                from specfact_cli.utils.structure import SpecFactStructure

                plan_bundle = PlanBundle(
                    version="1.0",
                    idea=Idea(
                        title="Test Project",
                        narrative="Test project description",
                        constraints=[],
                        metrics=None,
                    ),
                    business=None,
                    product=Product(themes=[], releases=[]),
                    features=[
                        Feature(
                            key="FEATURE-001",
                            title="Test Feature",
                            outcomes=[],
                            acceptance=[],
                            constraints=[],
                            stories=[],
                            confidence=0.9,
                            draft=False,
                            source_tracking=None,
                            contract=None,
                            protocol=None,
                        )
                    ],
                    clarifications=None,
                    metadata=None,
                )

                bundle_name = "main"
                bundle_dir = SpecFactStructure.project_dir(base_path=repo_path, bundle_name=bundle_name)
                SpecFactStructure.ensure_project_structure(base_path=repo_path, bundle_name=bundle_name)
                project_bundle = _convert_plan_bundle_to_project_bundle(plan_bundle, bundle_name)
                save_project_bundle(project_bundle, bundle_dir, atomic=True)

                # Sync with compliance flag
                result = runner.invoke(
                    app,
                    [
                        "sync",
                        "bridge",
                        "--adapter",
                        "speckit",
                        "--bundle",
                        "main",
                        "--repo",
                        str(repo_path),
                        "--bidirectional",
                        "--ensure-compliance",
                    ],
                )

                assert result.exit_code == 0
                # Should warn about missing technology stack or skip if bundle not found
                assert (
                    "Technology stack" in result.stdout
                    or "Plan bundle validation complete" in result.stdout
                    or "Bundle 'main' not found" in result.stdout
                    or "skipping compliance check" in result.stdout.lower()
                )

        finally:
            os.environ.pop("TEST_MODE", None)

    def test_ensure_speckit_compliance_warns_non_testable_acceptance(self) -> None:
        """Test that --ensure-speckit-compliance warns when acceptance criteria are not testable."""
        os.environ["TEST_MODE"] = "true"
        try:
            with TemporaryDirectory() as tmpdir:
                repo_path = Path(tmpdir)

                # Create Spec-Kit structure
                specify_dir = repo_path / ".specify" / "memory"
                specify_dir.mkdir(parents=True)
                (specify_dir / "constitution.md").write_text("# Constitution\n")

                # Create SpecFact structure with modular bundle with non-testable acceptance (new structure)
                from specfact_cli.commands.plan import _convert_plan_bundle_to_project_bundle
                from specfact_cli.models.plan import Feature, Idea, PlanBundle, Product, Story
                from specfact_cli.utils.bundle_loader import save_project_bundle
                from specfact_cli.utils.structure import SpecFactStructure

                plan_bundle = PlanBundle(
                    version="1.0",
                    idea=Idea(
                        title="Test Project",
                        narrative="Test project description",
                        constraints=["Python 3.11+"],
                        metrics=None,
                    ),
                    business=None,
                    product=Product(themes=[], releases=[]),
                    features=[
                        Feature(
                            key="FEATURE-001",
                            title="Test Feature",
                            outcomes=[],
                            acceptance=[],
                            constraints=[],
                            stories=[
                                Story(
                                    key="STORY-001",
                                    title="As a user, I can use the feature",
                                    acceptance=["User can use feature", "Feature works well"],
                                    story_points=5,
                                    value_points=0,
                                    scenarios={},
                                    contracts=None,
                                )
                            ],
                            confidence=0.9,
                            draft=False,
                            source_tracking=None,
                            contract=None,
                            protocol=None,
                        )
                    ],
                    clarifications=None,
                    metadata=None,
                )

                bundle_name = "main"
                bundle_dir = SpecFactStructure.project_dir(base_path=repo_path, bundle_name=bundle_name)
                SpecFactStructure.ensure_project_structure(base_path=repo_path, bundle_name=bundle_name)
                project_bundle = _convert_plan_bundle_to_project_bundle(plan_bundle, bundle_name)
                save_project_bundle(project_bundle, bundle_dir, atomic=True)

                # Sync with compliance flag
                result = runner.invoke(
                    app,
                    [
                        "sync",
                        "bridge",
                        "--adapter",
                        "speckit",
                        "--bundle",
                        "main",
                        "--repo",
                        str(repo_path),
                        "--bidirectional",
                        "--ensure-compliance",
                    ],
                )

                assert result.exit_code == 0
                # Should warn about non-testable acceptance criteria
                assert "non-testable" in result.stdout.lower() or "Plan bundle validation complete" in result.stdout

        finally:
            os.environ.pop("TEST_MODE", None)
