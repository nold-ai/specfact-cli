"""
End-to-end tests for backlog refinement.

Tests the complete workflow from arbitrary DevOps backlog input to refined structured format.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from beartype import beartype

from specfact_cli.backlog.ai_refiner import BacklogAIRefiner
from specfact_cli.backlog.converter import convert_ado_work_item_to_backlog_item, convert_github_issue_to_backlog_item
from specfact_cli.backlog.template_detector import TemplateDetector
from specfact_cli.templates.registry import TemplateRegistry


@pytest.fixture
def full_template_registry(tmp_path: Path) -> TemplateRegistry:
    """Create template registry with all default templates."""
    registry = TemplateRegistry()

    defaults_dir = tmp_path / "templates" / "defaults"
    defaults_dir.mkdir(parents=True)

    # User story template
    (defaults_dir / "user_story_v1.yaml").write_text("""template_id: user_story_v1
name: User Story
scope: corporate
required_sections:
  - As a
  - I want
  - So that
  - Acceptance Criteria
body_patterns:
  as_a: "As a [^,]+ I want"
title_patterns:
  - "^.*[Uu]ser [Ss]tory.*$"
""")

    # Defect template
    (defaults_dir / "defect_v1.yaml").write_text("""template_id: defect_v1
name: Defect
scope: corporate
required_sections:
  - Description
  - Steps to Reproduce
  - Expected Behavior
  - Actual Behavior
body_patterns:
  steps: "[Ss]teps? to [Rr]eproduce"
title_patterns:
  - "^.*[Bb]ug.*$"
""")

    registry.load_templates_from_directory(defaults_dir)
    return registry


class TestBacklogRefinementE2E:
    """End-to-end tests for backlog refinement."""

    @beartype
    def test_e2e_github_issue_to_user_story(self, full_template_registry: TemplateRegistry) -> None:
        """E2E: Convert arbitrary GitHub issue → detect → refine → apply."""
        # Simulate arbitrary DevOps team input
        arbitrary_github_issue = {
            "number": 100,
            "html_url": "https://github.com/org/repo/issues/100",
            "title": "We need a way for users to authenticate",
            "body": """Hi team,
Our users are asking for authentication. Currently they can't log in.
Can we add this feature? It's been requested multiple times.

Let me know if you need more details.

Thanks!""",
            "state": "open",
            "assignees": [{"login": "dev1"}],
            "labels": [{"name": "feature"}, {"name": "priority"}],
            "created_at": "2024-01-18T10:00:00Z",
            "updated_at": "2024-01-19T14:30:00Z",
        }

        # Step 1: Convert to BacklogItem
        backlog_item = convert_github_issue_to_backlog_item(arbitrary_github_issue)

        assert backlog_item.id == "100"
        assert backlog_item.provider == "github"
        assert "authenticate" in backlog_item.title.lower() or "authentication" in backlog_item.title.lower()

        # Step 2: Detect template
        detector = TemplateDetector(full_template_registry)
        detection_result = detector.detect_template(backlog_item)

        # Arbitrary input should have low confidence
        assert detection_result.confidence < 0.6
        assert backlog_item.needs_refinement is True

        # Step 3: Generate refinement prompt
        refiner = BacklogAIRefiner()
        template = full_template_registry.get_template("user_story_v1")
        assert template is not None

        prompt = refiner.generate_refinement_prompt(backlog_item, template)

        # Verify prompt contains necessary information
        assert backlog_item.title in prompt
        assert backlog_item.body_markdown in prompt
        assert template.name in prompt

        # Step 4: Simulate IDE AI copilot refinement
        # (In real scenario, IDE AI copilot would execute the prompt)
        refined_content = """## As a
registered user

## I want
to authenticate and log in to the system

## So that
I can access my account and protected resources

## Acceptance Criteria
- User can enter username and password
- User can click login button
- System validates credentials against database
- User is redirected to dashboard on successful login
- Error message is shown on invalid credentials"""

        # Step 5: Validate refined content
        validation_result = refiner.validate_and_score_refinement(
            refined_content, backlog_item.body_markdown, template, backlog_item
        )

        assert validation_result.confidence >= 0.85
        assert validation_result.has_todo_markers is False
        assert validation_result.has_notes_section is False

        # Step 6: Apply refinement
        backlog_item.refined_body = validation_result.refined_body
        backlog_item.detected_template = template.template_id
        backlog_item.template_confidence = validation_result.confidence
        backlog_item.apply_refinement()

        # Verify final state
        assert backlog_item.body_markdown == refined_content
        assert backlog_item.refinement_applied is True
        assert backlog_item.detected_template == "user_story_v1"
        assert backlog_item.template_confidence is not None and backlog_item.template_confidence >= 0.85

    @beartype
    def test_e2e_ado_work_item_to_defect(self, full_template_registry: TemplateRegistry) -> None:
        """E2E: Convert arbitrary ADO work item → detect → refine → apply."""
        # Simulate arbitrary DevOps team input
        arbitrary_ado_item = {
            "id": 200,
            "url": "https://dev.azure.com/org/proj/_apis/wit/workitems/200",
            "fields": {
                "System.Title": "Something is broken",
                "System.Description": """Users are reporting that the login page crashes.
It happens when they click the login button.
We need to fix this ASAP!""",
                "System.State": "Active",
                "System.WorkItemType": "Bug",
                "System.Tags": "bug;critical;production",
                "System.AssignedTo": {"displayName": "Dev Team", "uniqueName": "dev@example.com"},
                "System.IterationPath": "Sprint 2",
                "System.AreaPath": "Frontend",
            },
        }

        # Step 1: Convert to BacklogItem
        backlog_item = convert_ado_work_item_to_backlog_item(arbitrary_ado_item)

        assert backlog_item.id == "200"
        assert backlog_item.provider == "ado"
        assert "broken" in backlog_item.title.lower()

        # Step 2: Detect template
        detector = TemplateDetector(full_template_registry)
        detection_result = detector.detect_template(backlog_item)

        # Arbitrary input should have low confidence
        assert detection_result.confidence < 0.6

        # Step 3: Generate refinement prompt for defect template
        refiner = BacklogAIRefiner()
        template = full_template_registry.get_template("defect_v1")
        assert template is not None

        prompt = refiner.generate_refinement_prompt(backlog_item, template)

        assert backlog_item.title in prompt
        assert "broken" in prompt.lower()

        # Step 4: Simulate IDE AI copilot refinement
        refined_content = """## Description
The login page crashes when users click the login button.

## Steps to Reproduce
1. Navigate to the login page
2. Enter any credentials
3. Click the login button
4. Page crashes with error

## Expected Behavior
User should be logged in and redirected to dashboard.

## Actual Behavior
Page crashes with JavaScript error."""

        # Step 5: Validate refined content
        validation_result = refiner.validate_and_score_refinement(
            refined_content, backlog_item.body_markdown, template, backlog_item
        )

        assert validation_result.confidence >= 0.85

        # Step 6: Apply refinement
        backlog_item.refined_body = validation_result.refined_body
        backlog_item.detected_template = template.template_id
        backlog_item.template_confidence = validation_result.confidence
        backlog_item.apply_refinement()

        # Verify final state
        assert backlog_item.body_markdown == refined_content
        assert backlog_item.refinement_applied is True
        assert backlog_item.detected_template == "defect_v1"

    @beartype
    def test_e2e_round_trip_preservation(self, full_template_registry: TemplateRegistry) -> None:
        """E2E: Verify that original provider fields are preserved."""
        original_github_issue = {
            "number": 300,
            "html_url": "https://github.com/org/repo/issues/300",
            "title": "Feature request",
            "body": "We need this feature",
            "state": "open",
            "comments": 5,
            "milestone": {"title": "Sprint 1"},
            "user": {"login": "requester"},
        }

        backlog_item = convert_github_issue_to_backlog_item(original_github_issue)

        # Verify provider fields are preserved
        assert backlog_item.provider_fields["number"] == "300"
        assert backlog_item.provider_fields["comments"] == 5
        assert backlog_item.provider_fields["milestone"] is not None

        # Refine the item
        refiner = BacklogAIRefiner()
        template = full_template_registry.get_template("user_story_v1")
        assert template is not None

        refined_content = """## As a
user

## I want
this feature

## So that
I can accomplish my goal

## Acceptance Criteria
- Feature is available"""

        validation_result = refiner.validate_and_score_refinement(
            refined_content, backlog_item.body_markdown, template, backlog_item
        )

        backlog_item.refined_body = validation_result.refined_body
        backlog_item.apply_refinement()

        # Verify provider fields are still preserved after refinement
        assert backlog_item.provider_fields["number"] == "300"
        assert backlog_item.provider_fields["comments"] == 5
        assert "milestone" in backlog_item.provider_fields

    @beartype
    def test_e2e_sprint_release_extraction(self, full_template_registry: TemplateRegistry) -> None:
        """E2E: Verify sprint and release extraction from GitHub milestones and ADO iteration paths."""
        # Test GitHub milestone extraction
        github_issue_with_sprint = {
            "number": 400,
            "html_url": "https://github.com/org/repo/issues/400",
            "title": "Test Issue",
            "body": "",
            "state": "open",
            "milestone": {"title": "Sprint 3"},
        }

        backlog_item = convert_github_issue_to_backlog_item(github_issue_with_sprint)
        assert backlog_item.sprint == "Sprint 3"
        assert backlog_item.release is None

        # Test GitHub release milestone
        github_issue_with_release = {
            "number": 401,
            "html_url": "https://github.com/org/repo/issues/401",
            "title": "Test Issue",
            "body": "",
            "state": "open",
            "milestone": {"title": "Release 2.0"},
        }

        backlog_item = convert_github_issue_to_backlog_item(github_issue_with_release)
        assert backlog_item.release == "Release 2.0"
        assert backlog_item.sprint is None

        # Test ADO iteration path extraction
        ado_item_with_sprint_release = {
            "id": 500,
            "url": "https://dev.azure.com/org/proj/_apis/wit/workitems/500",
            "fields": {
                "System.Title": "Test Work Item",
                "System.Description": "",
                "System.State": "New",
                "System.IterationPath": "Project\\Release 1\\Sprint 1",
            },
        }

        backlog_item = convert_ado_work_item_to_backlog_item(ado_item_with_sprint_release)
        assert backlog_item.sprint == "Sprint 1"
        assert backlog_item.release == "Release 1"
        assert backlog_item.iteration == "Project\\Release 1\\Sprint 1"

    @beartype
    def test_e2e_template_resolution_with_filters(self, full_template_registry: TemplateRegistry) -> None:
        """E2E: Verify template resolution with persona/framework/provider filters."""
        # Add framework-specific template
        scrum_template = full_template_registry.get_template("user_story_v1")
        if scrum_template:
            # Create a scrum-specific version
            from specfact_cli.templates.registry import BacklogTemplate

            scrum_story = BacklogTemplate(
                template_id="scrum_story_v1",
                name="Scrum User Story",
                framework="scrum",
                required_sections=scrum_template.required_sections,
                body_patterns=scrum_template.body_patterns,
            )
            full_template_registry.register_template(scrum_story)

        detector = TemplateDetector(full_template_registry)

        item = convert_github_issue_to_backlog_item(
            {
                "number": 600,
                "html_url": "https://github.com/org/repo/issues/600",
                "title": "User Story: Add feature",
                "body": "## As a\nuser\n\n## I want\nto add features",
                "state": "open",
            }
        )

        # Test with framework filter
        result = detector.detect_template(item, provider="github", framework="scrum")
        # Should match scrum template if available, otherwise default
        assert result.template_id is not None
        assert result.confidence >= 0.5
