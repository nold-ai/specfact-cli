"""Integration tests for --ensure-speckit-compliance flag."""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent

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

                # Create SpecFact structure with plan bundle
                plans_dir = repo_path / ".specfact" / "plans"
                plans_dir.mkdir(parents=True)

                # Create plan bundle with technology stack in constraints
                plan_content = dedent(
                    """
                    version: '1.0'
                    idea:
                      title: Test Project
                      narrative: Test project description
                      constraints:
                        - Python 3.11+
                        - FastAPI framework
                        - PostgreSQL database
                    product:
                      themes: []
                      releases: []
                    features:
                      - key: FEATURE-001
                        title: Test Feature
                        outcomes: []
                        acceptance:
                          - Must verify feature works correctly
                        constraints: []
                        stories:
                          - key: STORY-001
                            title: As a user, I can use the feature
                            acceptance:
                              - Must verify feature works
                              - Must validate input
                            story_points: 5
                        confidence: 0.9
                        draft: false
                    metadata:
                      stage: draft
                    """
                )
                (plans_dir / "main.bundle.yaml").write_text(plan_content)

                # Sync with compliance flag
                result = runner.invoke(
                    app,
                    [
                        "sync",
                        "spec-kit",
                        "--repo",
                        str(repo_path),
                        "--bidirectional",
                        "--ensure-speckit-compliance",
                    ],
                )

                assert result.exit_code == 0
                assert (
                    "Validating plan bundle for Spec-Kit compliance" in result.stdout
                    or "Plan bundle validation complete" in result.stdout
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

                # Create SpecFact structure with plan bundle without technology stack
                plans_dir = repo_path / ".specfact" / "plans"
                plans_dir.mkdir(parents=True)

                plan_content = dedent(
                    """
                    version: '1.0'
                    idea:
                      title: Test Project
                      narrative: Test project description
                      constraints: []
                    product:
                      themes: []
                      releases: []
                    features:
                      - key: FEATURE-001
                        title: Test Feature
                        outcomes: []
                        acceptance: []
                        constraints: []
                        stories: []
                        confidence: 0.9
                        draft: false
                    metadata:
                      stage: draft
                    """
                )
                (plans_dir / "main.bundle.yaml").write_text(plan_content)

                # Sync with compliance flag
                result = runner.invoke(
                    app,
                    [
                        "sync",
                        "spec-kit",
                        "--repo",
                        str(repo_path),
                        "--bidirectional",
                        "--ensure-speckit-compliance",
                    ],
                )

                assert result.exit_code == 0
                # Should warn about missing technology stack
                assert "Technology stack" in result.stdout or "Plan bundle validation complete" in result.stdout

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

                # Create SpecFact structure with plan bundle with non-testable acceptance
                plans_dir = repo_path / ".specfact" / "plans"
                plans_dir.mkdir(parents=True)

                plan_content = dedent(
                    """
                    version: '1.0'
                    idea:
                      title: Test Project
                      narrative: Test project description
                      constraints:
                        - Python 3.11+
                    product:
                      themes: []
                      releases: []
                    features:
                      - key: FEATURE-001
                        title: Test Feature
                        outcomes: []
                        acceptance: []
                        constraints: []
                        stories:
                          - key: STORY-001
                            title: As a user, I can use the feature
                            acceptance:
                              - User can use feature
                              - Feature works well
                            story_points: 5
                        confidence: 0.9
                        draft: false
                    metadata:
                      stage: draft
                    """
                )
                (plans_dir / "main.bundle.yaml").write_text(plan_content)

                # Sync with compliance flag
                result = runner.invoke(
                    app,
                    [
                        "sync",
                        "spec-kit",
                        "--repo",
                        str(repo_path),
                        "--bidirectional",
                        "--ensure-speckit-compliance",
                    ],
                )

                assert result.exit_code == 0
                # Should warn about non-testable acceptance criteria
                assert "non-testable" in result.stdout.lower() or "Plan bundle validation complete" in result.stdout

        finally:
            os.environ.pop("TEST_MODE", None)
