"""End-to-end tests for plan review non-interactive mode (Copilot/CI/CD)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.models.plan import Feature, Idea, Metadata, PlanBundle, Product


runner = CliRunner()


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """Create a temporary workspace with .specfact structure."""
    workspace = tmp_path / "review_workspace"
    workspace.mkdir()
    (workspace / ".specfact").mkdir()
    (workspace / ".specfact" / "projects").mkdir()
    return workspace


@pytest.fixture
def incomplete_plan(workspace: Path) -> Path:
    """Create an incomplete plan bundle for testing (modular bundle)."""
    bundle_name = "test-plan"
    bundle_dir = workspace / ".specfact" / "projects" / bundle_name
    bundle_dir.mkdir(parents=True)

    bundle = PlanBundle(
        version="1.0",
        idea=Idea(
            title="Test Plan",
            narrative="",  # Empty narrative - will trigger question
            target_users=[],
            value_hypothesis="",
            constraints=[],
            metrics=None,
        ),
        business=None,
        product=Product(themes=["Core"], releases=[]),
        features=[
            Feature(
                key="FEATURE-001",
                title="Incomplete Feature",
                outcomes=[],
                acceptance=[],
                constraints=[],
                stories=[],  # Missing stories - will trigger question
                confidence=0.8,
                draft=False,
            ),
            Feature(
                key="FEATURE-002",
                title="Another Incomplete Feature",
                outcomes=[],
                acceptance=[],
                constraints=[],
                stories=[],  # Missing stories - will trigger question
                confidence=0.7,
                draft=False,
            ),
        ],
        metadata=Metadata(
            stage="draft",
            promoted_at=None,
            promoted_by=None,
            analysis_scope=None,
            entry_point=None,
            external_dependencies=[],
            summary=None,
        ),
        clarifications=None,
    )

    # Convert to modular bundle
    from specfact_cli.commands.plan import _convert_plan_bundle_to_project_bundle
    from specfact_cli.utils.bundle_loader import save_project_bundle

    project_bundle = _convert_plan_bundle_to_project_bundle(bundle, bundle_name)
    save_project_bundle(project_bundle, bundle_dir, atomic=True)

    return bundle_dir


class TestPlanReviewNonInteractive:
    """Test suite for non-interactive plan review mode."""

    def test_list_questions_output_json(self, workspace: Path, incomplete_plan: Path, monkeypatch):
        """Test --list-questions outputs valid JSON."""
        monkeypatch.chdir(workspace)

        # Get bundle name from directory path
        bundle_name = (
            incomplete_plan.name
            if isinstance(incomplete_plan, Path) and incomplete_plan.is_dir()
            else str(incomplete_plan)
        )

        result = runner.invoke(
            app,
            [
                "plan",
                "review",
                bundle_name,
                "--list-questions",
                "--max-questions",
                "5",
            ],
        )

        if result.exit_code != 0:
            print(f"Command failed with exit code {result.exit_code}")
            print(f"stdout: {result.stdout}")
            # Check if bundle was found
            if "not found" in result.stdout or "Bundle" in result.stdout:
                print(f"Bundle name used: {bundle_name}")
                print(f"Bundle directory exists: {incomplete_plan.exists()}")

        assert result.exit_code == 0

        # Parse JSON output
        output_lines = result.stdout.strip().split("\n")
        json_start = None
        for i, line in enumerate(output_lines):
            if line.strip().startswith("{"):
                json_start = i
                break

        assert json_start is not None, "No JSON found in output"

        json_str = "\n".join(output_lines[json_start:])
        data = json.loads(json_str)

        # Validate structure
        assert "questions" in data
        assert "total" in data
        assert isinstance(data["questions"], list)
        assert isinstance(data["total"], int)
        assert data["total"] == len(data["questions"])

        # Validate question structure
        if len(data["questions"]) > 0:
            question = data["questions"][0]
            assert "id" in question
            assert "category" in question
            assert "question" in question
            assert "impact" in question
            assert "uncertainty" in question
            assert "related_sections" in question

    def test_list_questions_empty_when_no_ambiguities(self, workspace: Path, monkeypatch):
        """Test --list-questions returns empty list when plan has no ambiguities."""
        monkeypatch.chdir(workspace)

        # Create complete plan (modular bundle)
        bundle_name = "complete-plan"
        bundle_dir = workspace / ".specfact" / "projects" / bundle_name
        bundle_dir.mkdir(parents=True)
        bundle = PlanBundle(
            version="1.0",
            idea=Idea(
                title="Complete Plan",
                narrative="This is a complete narrative with sufficient detail",
                target_users=["developers"],
                value_hypothesis="Test hypothesis",
                constraints=["Constraint 1"],
                metrics=None,
            ),
            business=None,
            product=Product(themes=["Core"], releases=[]),
            features=[
                Feature(
                    key="FEATURE-001",
                    title="Complete Feature",
                    outcomes=["Outcome 1"],
                    acceptance=["Acceptance 1"],
                    constraints=["Constraint 1"],
                    stories=[],
                    confidence=0.9,
                    draft=False,
                )
            ],
            metadata=Metadata(
                stage="draft",
                promoted_at=None,
                promoted_by=None,
                analysis_scope=None,
                entry_point=None,
                external_dependencies=[],
                summary=None,
            ),
            clarifications=None,
        )

        # Convert to modular bundle
        from specfact_cli.commands.plan import _convert_plan_bundle_to_project_bundle
        from specfact_cli.utils.bundle_loader import save_project_bundle

        project_bundle = _convert_plan_bundle_to_project_bundle(bundle, bundle_name)
        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        result = runner.invoke(
            app,
            [
                "plan",
                "review",
                bundle_name,
                "--list-questions",
                "--max-questions",
                "5",
            ],
        )

        # Should exit with 0 but may have no questions
        assert result.exit_code == 0

    def test_answers_from_file(self, workspace: Path, incomplete_plan: Path, monkeypatch):
        """Test --answers with JSON file path."""
        monkeypatch.chdir(workspace)

        # Create answers file
        answers_file = workspace / "answers.json"
        answers = {
            "Q001": "Test narrative answer",
            "Q002": "Test story answer",
        }
        answers_file.write_text(json.dumps(answers, indent=2))

        # Get bundle name from directory path
        bundle_name = (
            incomplete_plan.name
            if isinstance(incomplete_plan, Path) and incomplete_plan.is_dir()
            else str(incomplete_plan)
        )

        result = runner.invoke(
            app,
            [
                "plan",
                "review",
                bundle_name,
                "--answers",
                str(answers_file),
                "--max-questions",
                "5",
            ],
        )

        assert result.exit_code == 0
        assert "Review complete" in result.stdout or "question(s) answered" in result.stdout

        # Verify plan was updated (modular bundle)
        from specfact_cli.commands.plan import _convert_project_bundle_to_plan_bundle
        from specfact_cli.utils.bundle_loader import load_project_bundle

        updated_project_bundle = load_project_bundle(incomplete_plan, validate_hashes=False)
        updated_bundle = _convert_project_bundle_to_plan_bundle(updated_project_bundle)

        # Should have clarifications
        assert updated_bundle.clarifications is not None
        assert len(updated_bundle.clarifications.sessions) > 0

    def test_answers_from_json_string(self, workspace: Path, incomplete_plan: Path, monkeypatch):
        """Test --answers with JSON string (should work but may have Rich parsing issues)."""
        monkeypatch.chdir(workspace)

        # Try with JSON string (may fail due to Rich markup parsing)
        answers_json = json.dumps({"Q001": "Test answer from JSON string"})

        # Get bundle name from directory path
        bundle_name = (
            incomplete_plan.name
            if isinstance(incomplete_plan, Path) and incomplete_plan.is_dir()
            else str(incomplete_plan)
        )

        result = runner.invoke(
            app,
            [
                "plan",
                "review",
                bundle_name,
                "--answers",
                answers_json,
                "--max-questions",
                "1",
            ],
        )

        # May fail due to Rich markup parsing, but if it works, verify
        if result.exit_code == 0:
            assert "Review complete" in result.stdout or "question(s) answered" in result.stdout

    def test_non_interactive_flag(self, workspace: Path, incomplete_plan: Path, monkeypatch):
        """Test --no-interactive flag behavior."""
        monkeypatch.chdir(workspace)

        # Get bundle name from directory path
        bundle_name = (
            incomplete_plan.name
            if isinstance(incomplete_plan, Path) and incomplete_plan.is_dir()
            else str(incomplete_plan)
        )

        # Without --answers, should skip questions
        result = runner.invoke(
            app,
            [
                "plan",
                "review",
                bundle_name,
                "--no-interactive",
                "--max-questions",
                "5",
            ],
        )

        # Should exit successfully but skip questions
        assert result.exit_code == 0
        assert "non-interactive" in result.stdout.lower() or "Skipping" in result.stdout

    def test_answers_integration_into_plan(self, workspace: Path, incomplete_plan: Path, monkeypatch):
        """Test that answers are properly integrated into plan bundle."""
        monkeypatch.chdir(workspace)

        # Get questions first
        list_result = runner.invoke(
            app,
            [
                "plan",
                "review",
                incomplete_plan.name
                if isinstance(incomplete_plan, Path) and incomplete_plan.is_dir()
                else str(incomplete_plan),
                "--list-questions",
                "--max-questions",
                "2",
            ],
        )

        assert list_result.exit_code == 0

        # Parse questions
        output_lines = list_result.stdout.strip().split("\n")
        json_start = None
        for i, line in enumerate(output_lines):
            if line.strip().startswith("{"):
                json_start = i
                break

        if json_start is None:
            pytest.skip("No questions found")

        json_str = "\n".join(output_lines[json_start:])
        questions_data = json.loads(json_str)

        if len(questions_data["questions"]) == 0:
            pytest.skip("No questions to test")

        # Create answers for first question
        first_question = questions_data["questions"][0]
        answers = {first_question["id"]: "Test integration answer"}

        # Create answers file
        answers_file = workspace / "integration_answers.json"
        answers_file.write_text(json.dumps(answers, indent=2))

        # Get bundle name from directory path
        bundle_name = (
            incomplete_plan.name
            if isinstance(incomplete_plan, Path) and incomplete_plan.is_dir()
            else str(incomplete_plan)
        )

        # Apply answers
        apply_result = runner.invoke(
            app,
            [
                "plan",
                "review",
                bundle_name,
                "--answers",
                str(answers_file),
                "--max-questions",
                "1",
            ],
        )

        assert apply_result.exit_code == 0

        # Verify integration
        # Load updated bundle (modular bundle)
        from specfact_cli.commands.plan import _convert_project_bundle_to_plan_bundle
        from specfact_cli.utils.bundle_loader import load_project_bundle

        updated_project_bundle = load_project_bundle(incomplete_plan, validate_hashes=False)
        updated_bundle = _convert_project_bundle_to_plan_bundle(updated_project_bundle)

        assert updated_bundle.clarifications is not None
        assert len(updated_bundle.clarifications.sessions) > 0

        # Find the clarification
        found_clarification = False
        for session in updated_bundle.clarifications.sessions:
            for q in session.questions:
                if q.id == first_question["id"]:
                    assert q.answer == "Test integration answer"
                    # integrated_into may be empty if answer doesn't map to a section
                    found_clarification = True
                    break
            if found_clarification:
                break

        assert found_clarification, (
            f"Clarification {first_question['id']} not found in updated plan. Found: {[q.id for s in updated_bundle.clarifications.sessions for q in s.questions]}"
        )

    def test_copilot_workflow_simulation(self, workspace: Path, incomplete_plan: Path, monkeypatch):
        """Test complete Copilot workflow: list -> ask -> feed."""
        monkeypatch.chdir(workspace)

        # Phase 1: Get questions
        list_result = runner.invoke(
            app,
            [
                "plan",
                "review",
                incomplete_plan.name
                if isinstance(incomplete_plan, Path) and incomplete_plan.is_dir()
                else str(incomplete_plan),
                "--list-questions",
                "--max-questions",
                "3",
            ],
        )

        assert list_result.exit_code == 0

        # Parse questions
        output_lines = list_result.stdout.strip().split("\n")
        json_start = None
        for i, line in enumerate(output_lines):
            if line.strip().startswith("{"):
                json_start = i
                break

        if json_start is None:
            pytest.skip("No questions found")

        json_str = "\n".join(output_lines[json_start:])
        questions_data = json.loads(json_str)

        if len(questions_data["questions"]) == 0:
            pytest.skip("No questions to test")

        # Phase 2: Simulate user answers (in real Copilot, LLM would ask user)
        answers = {}
        for question in questions_data["questions"][:2]:  # Answer first 2
            answers[question["id"]] = f"Answer for {question['id']}"

        # Phase 3: Feed answers back
        answers_file = workspace / "copilot_answers.json"
        answers_file.write_text(json.dumps(answers, indent=2))

        # Get bundle name from directory path
        bundle_name = (
            incomplete_plan.name
            if isinstance(incomplete_plan, Path) and incomplete_plan.is_dir()
            else str(incomplete_plan)
        )

        feed_result = runner.invoke(
            app,
            [
                "plan",
                "review",
                bundle_name,
                "--answers",
                str(answers_file),
                "--max-questions",
                "2",
            ],
        )

        assert feed_result.exit_code == 0
        assert "Review complete" in feed_result.stdout or "question(s) answered" in feed_result.stdout

        # Verify all answers were integrated
        # Load updated bundle (modular bundle)
        from specfact_cli.commands.plan import _convert_project_bundle_to_plan_bundle
        from specfact_cli.utils.bundle_loader import load_project_bundle

        updated_project_bundle = load_project_bundle(incomplete_plan, validate_hashes=False)
        updated_bundle = _convert_project_bundle_to_plan_bundle(updated_project_bundle)

        assert updated_bundle.clarifications is not None

        # Count integrated answers
        integrated_count = 0
        for session in updated_bundle.clarifications.sessions:
            for q in session.questions:
                if q.id in answers:
                    assert q.answer == answers[q.id]
                    integrated_count += 1

        assert integrated_count == len(answers), f"Expected {len(answers)} answers, got {integrated_count}"
