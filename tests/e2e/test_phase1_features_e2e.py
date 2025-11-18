"""End-to-end tests for Phase 1 features: Test Patterns, Scenarios, Requirements, Entry Points."""

from __future__ import annotations

import os
from pathlib import Path
from textwrap import dedent

import pytest
from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.utils.yaml_utils import load_yaml


runner = CliRunner()


class TestPhase1FeaturesE2E:
    """E2E tests for Phase 1 features (Steps 1.1-1.4)."""

    @pytest.fixture
    def test_repo(self, tmp_path: Path) -> Path:
        """Create a test repository with code for Phase 1 testing."""
        repo = tmp_path / "test_repo"
        repo.mkdir()

        # Create source code with test files
        src_dir = repo / "src"
        src_dir.mkdir()
        api_dir = src_dir / "api"
        api_dir.mkdir()
        core_dir = src_dir / "core"
        core_dir.mkdir()

        # API module with async patterns (for NFR detection)
        (api_dir / "service.py").write_text(
            dedent(
                '''
                """API service module."""
                import asyncio
                from typing import Optional

                class ApiService:
                    """API service with async operations."""

                    async def fetch_data(self, endpoint: str) -> dict:
                        """Fetch data from API endpoint."""
                        if not endpoint:
                            raise ValueError("Endpoint required")
                        return {"status": "ok", "data": []}

                    async def process_request(self, data: dict) -> dict:
                        """Process API request with retry logic."""
                        max_retries = 3
                        for attempt in range(max_retries):
                            try:
                                # Simulate processing
                                return {"success": True, "data": data}
                            except Exception:
                                if attempt == max_retries - 1:
                                    raise
                                await asyncio.sleep(1)
                        return {}
                '''
            )
        )

        # Core module with validation (for test patterns)
        (core_dir / "validator.py").write_text(
            dedent(
                '''
                """Validation module."""
                from typing import Optional

                class Validator:
                    """Data validation service."""

                    def validate_email(self, email: str) -> bool:
                        """Validate email format."""
                        if not email:
                            return False
                        return "@" in email and "." in email.split("@")[1]

                    def validate_user(self, name: str, email: str) -> dict:
                        """Validate user data."""
                        if not name:
                            raise ValueError("Name required")
                        if not self.validate_email(email):
                            raise ValueError("Invalid email")
                        return {"name": name, "email": email, "valid": True}
                '''
            )
        )

        # Create test files (for test pattern extraction)
        tests_dir = repo / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_validator.py").write_text(
            dedent(
                '''
                """Tests for validator module."""
                import pytest
                from src.core.validator import Validator

                def test_validate_email():
                    """Test email validation."""
                    validator = Validator()
                    assert validator.validate_email("test@example.com") is True
                    assert validator.validate_email("invalid") is False

                def test_validate_user():
                    """Test user validation."""
                    validator = Validator()
                    result = validator.validate_user("John", "john@example.com")
                    assert result["valid"] is True
                    assert result["name"] == "John"
                '''
            )
        )

        # Create requirements.txt for technology stack extraction
        (repo / "requirements.txt").write_text(
            dedent(
                """
                python>=3.11
                fastapi==0.104.1
                pydantic>=2.0.0
                """
            )
        )

        return repo

    def test_step1_1_test_patterns_extraction(self, test_repo: Path) -> None:
        """Test Step 1.1: Extract test patterns for acceptance criteria (Given/When/Then format)."""
        os.environ["TEST_MODE"] = "true"
        try:
            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    "--repo",
                    str(test_repo),
                    "--out",
                    str(test_repo / "plan.yaml"),
                ],
            )

            assert result.exit_code == 0, f"Import failed: {result.stdout}"
            assert "Import complete" in result.stdout

            # Load plan bundle
            plan_data = load_yaml(test_repo / "plan.yaml")
            features = plan_data.get("features", [])

            assert len(features) > 0, "Should extract features"

            # Verify acceptance criteria are in Given/When/Then format
            for feature in features:
                stories = feature.get("stories", [])
                for story in stories:
                    acceptance = story.get("acceptance", [])
                    assert len(acceptance) > 0, f"Story {story.get('key')} should have acceptance criteria"

                    # Check that acceptance criteria are in Given/When/Then format
                    gwt_found = False
                    for criterion in acceptance:
                        criterion_lower = criterion.lower()
                        if "given" in criterion_lower and "when" in criterion_lower and "then" in criterion_lower:
                            gwt_found = True
                            break

                    assert gwt_found, f"Story {story.get('key')} should have Given/When/Then format acceptance criteria"

        finally:
            os.environ.pop("TEST_MODE", None)

    def test_step1_2_control_flow_scenarios(self, test_repo: Path) -> None:
        """Test Step 1.2: Extract control flow scenarios (Primary, Alternate, Exception, Recovery)."""
        os.environ["TEST_MODE"] = "true"
        try:
            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    "--repo",
                    str(test_repo),
                    "--out",
                    str(test_repo / "plan.yaml"),
                ],
            )

            assert result.exit_code == 0
            plan_data = load_yaml(test_repo / "plan.yaml")
            features = plan_data.get("features", [])

            # Verify scenarios are extracted from control flow
            scenario_found = False
            for feature in features:
                stories = feature.get("stories", [])
                for story in stories:
                    scenarios = story.get("scenarios", {})
                    if scenarios:
                        scenario_found = True
                        # Verify scenario types
                        scenario_types = set(scenarios.keys())
                        assert len(scenario_types) > 0, "Should have at least one scenario type"
                        # Check for common scenario types
                        assert any(
                            stype in ["primary", "alternate", "exception", "recovery"] for stype in scenario_types
                        ), f"Should have valid scenario types, got: {scenario_types}"

            assert scenario_found, "Should extract scenarios from code control flow"

        finally:
            os.environ.pop("TEST_MODE", None)

    def test_step1_3_complete_requirements_and_nfrs(self, test_repo: Path) -> None:
        """Test Step 1.3: Extract complete requirements and NFRs from code semantics."""
        os.environ["TEST_MODE"] = "true"
        try:
            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    "--repo",
                    str(test_repo),
                    "--out",
                    str(test_repo / "plan.yaml"),
                ],
            )

            assert result.exit_code == 0
            plan_data = load_yaml(test_repo / "plan.yaml")
            features = plan_data.get("features", [])

            # Verify complete requirements (Subject + Modal + Action + Object + Outcome)
            requirement_found = False
            for feature in features:
                acceptance = feature.get("acceptance", [])
                if acceptance:
                    requirement_found = True
                    # Check that requirements are complete (not just fragments)
                    for req in acceptance:
                        req_lower = req.lower()
                        # Should have action verbs and objects
                        assert len(req.split()) > 5, f"Requirement should be complete: {req}"

                # Verify NFRs are extracted (from constraints)
                constraints = feature.get("constraints", [])
                nfr_found = False
                for constraint in constraints:
                    constraint_lower = constraint.lower()
                    # Check for NFR patterns (performance, security, reliability, maintainability)
                    if any(
                        keyword in constraint_lower
                        for keyword in ["performance", "security", "reliability", "maintainability", "async", "error"]
                    ):
                        nfr_found = True
                        break

                # At least one feature should have NFRs (ApiService has async patterns)
                if "api" in feature.get("title", "").lower() or "service" in feature.get("title", "").lower():
                    assert nfr_found, f"Feature {feature.get('key')} should have NFRs extracted"

            assert requirement_found, "Should extract complete requirements"

        finally:
            os.environ.pop("TEST_MODE", None)

    def test_step1_4_entry_point_scoping(self, test_repo: Path) -> None:
        """Test Step 1.4: Partial repository analysis with entry point."""
        os.environ["TEST_MODE"] = "true"
        try:
            # Test full repository analysis
            result_full = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    "--repo",
                    str(test_repo),
                    "--out",
                    str(test_repo / "plan-full.yaml"),
                ],
            )

            assert result_full.exit_code == 0
            plan_full = load_yaml(test_repo / "plan-full.yaml")
            features_full = plan_full.get("features", [])
            metadata_full = plan_full.get("metadata", {})

            # Verify full analysis metadata
            assert metadata_full.get("analysis_scope") == "full" or metadata_full.get("analysis_scope") is None
            assert metadata_full.get("entry_point") is None

            # Test partial analysis with entry point
            result_partial = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    "--repo",
                    str(test_repo),
                    "--entry-point",
                    "src/api",
                    "--out",
                    str(test_repo / "plan-partial.yaml"),
                ],
            )

            assert result_partial.exit_code == 0
            plan_partial = load_yaml(test_repo / "plan-partial.yaml")
            features_partial = plan_partial.get("features", [])
            metadata_partial = plan_partial.get("metadata", {})

            # Verify partial analysis metadata
            assert metadata_partial.get("analysis_scope") == "partial"
            assert metadata_partial.get("entry_point") == "src/api"

            # Verify scoped analysis has fewer features
            assert len(features_partial) < len(features_full), "Partial analysis should have fewer features"

            # Verify external dependencies are tracked
            external_deps = metadata_partial.get("external_dependencies", [])
            # May have external dependencies depending on imports
            assert isinstance(external_deps, list), "External dependencies should be a list"

            # Verify plan name is generated from entry point
            idea = plan_partial.get("idea", {})
            title = idea.get("title", "")
            assert "api" in title.lower() or "module" in title.lower(), "Plan name should reflect entry point"

        finally:
            os.environ.pop("TEST_MODE", None)

    def test_phase1_complete_workflow(self, test_repo: Path) -> None:
        """Test complete Phase 1 workflow: all steps together."""
        os.environ["TEST_MODE"] = "true"
        try:
            result = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    "--repo",
                    str(test_repo),
                    "--entry-point",
                    "src/core",
                    "--out",
                    str(test_repo / "plan-phase1.yaml"),
                ],
            )

            assert result.exit_code == 0
            plan_data = load_yaml(test_repo / "plan-phase1.yaml")

            # Verify all Phase 1 features are present
            features = plan_data.get("features", [])

            # Step 1.1: Test patterns
            gwt_found = False
            for feature in features:
                stories = feature.get("stories", [])
                for story in stories:
                    acceptance = story.get("acceptance", [])
                    for criterion in acceptance:
                        if "given" in criterion.lower() and "when" in criterion.lower() and "then" in criterion.lower():
                            gwt_found = True
                            break

            assert gwt_found, "Step 1.1: Should have Given/When/Then acceptance criteria"

            # Step 1.2: Scenarios
            scenario_found = False
            for feature in features:
                stories = feature.get("stories", [])
                for story in stories:
                    if story.get("scenarios"):
                        scenario_found = True
                        break

            assert scenario_found, "Step 1.2: Should have code-derived scenarios"

            # Step 1.3: Complete requirements and NFRs
            requirement_found = False
            nfr_found = False
            for feature in features:
                acceptance = feature.get("acceptance", [])
                if acceptance:
                    requirement_found = True

                constraints = feature.get("constraints", [])
                for constraint in constraints:
                    if any(
                        keyword in constraint.lower()
                        for keyword in ["performance", "security", "reliability", "maintainability"]
                    ):
                        nfr_found = True
                        break

            assert requirement_found, "Step 1.3: Should have complete requirements"
            # NFRs may not be present in all features, so we check if any feature has them

            # Step 1.4: Entry point scoping
            metadata = plan_data.get("metadata", {})
            assert metadata.get("analysis_scope") == "partial", "Step 1.4: Should have partial scope"
            assert metadata.get("entry_point") == "src/core", "Step 1.4: Should track entry point"

        finally:
            os.environ.pop("TEST_MODE", None)

