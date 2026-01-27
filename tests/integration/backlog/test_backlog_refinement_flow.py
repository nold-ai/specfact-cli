"""
Integration tests for backlog refinement flow.

Tests the complete flow: fetch → detect → refine → validate → apply.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from beartype import beartype

from specfact_cli.backlog.ai_refiner import BacklogAIRefiner
from specfact_cli.backlog.converter import convert_github_issue_to_backlog_item
from specfact_cli.backlog.template_detector import TemplateDetector
from specfact_cli.templates.registry import TemplateRegistry


@pytest.fixture
def template_registry_with_defaults(tmp_path: Path) -> TemplateRegistry:
    """Create template registry with default templates loaded."""
    registry = TemplateRegistry()

    # Create defaults directory structure
    defaults_dir = tmp_path / "templates" / "defaults"
    defaults_dir.mkdir(parents=True)

    # Create user story template
    user_story_file = defaults_dir / "user_story_v1.yaml"
    user_story_file.write_text("""template_id: user_story_v1
name: User Story
description: Standard user story template
scope: corporate
required_sections:
  - As a
  - I want
  - So that
  - Acceptance Criteria
optional_sections:
  - Notes
body_patterns:
  as_a: "As a [^,]+ I want"
title_patterns:
  - "^.*[Uu]ser [Ss]tory.*$"
""")

    registry.load_templates_from_directory(defaults_dir)
    return registry


class TestBacklogRefinementFlow:
    """Test complete backlog refinement flow."""

    @beartype
    def test_refine_arbitrary_github_issue_to_user_story(
        self, template_registry_with_defaults: TemplateRegistry
    ) -> None:
        """Test refining arbitrary GitHub issue into user story template."""
        # Step 1: Convert arbitrary GitHub issue to BacklogItem
        arbitrary_issue = {
            "number": 123,
            "html_url": "https://github.com/test/repo/issues/123",
            "title": "Need login feature",
            "body": """Hey team,
We need to add a login feature. Users are asking for it.
Can someone implement this?

Thanks!""",
            "state": "open",
            "assignees": [],
            "labels": [],
        }

        backlog_item = convert_github_issue_to_backlog_item(arbitrary_issue)

        # Step 2: Detect template (should have low/no confidence)
        detector = TemplateDetector(template_registry_with_defaults)
        detection_result = detector.detect_template(backlog_item)

        assert detection_result.confidence < 0.6  # Low confidence for arbitrary input
        assert backlog_item.needs_refinement is True

        # Step 3: Generate refinement prompt
        refiner = BacklogAIRefiner()
        template = template_registry_with_defaults.get_template("user_story_v1")
        assert template is not None

        prompt = refiner.generate_refinement_prompt(backlog_item, template)

        assert "Need login feature" in prompt
        assert "login feature" in prompt
        assert "As a" in prompt
        assert "I want" in prompt

        # Step 4: Simulate refined content from IDE AI copilot
        refined_content = """## As a
user

## I want
to log in to the system

## So that
I can access my account and protected resources

## Acceptance Criteria
- User can enter username and password
- User can click login button
- System validates credentials
- User is redirected to dashboard on success"""

        # Step 5: Validate refined content
        validation_result = refiner.validate_and_score_refinement(
            refined_content, backlog_item.body_markdown, template, backlog_item
        )

        assert validation_result.confidence >= 0.85
        assert validation_result.has_todo_markers is False

        # Step 6: Apply refinement
        backlog_item.refined_body = validation_result.refined_body
        backlog_item.detected_template = template.template_id
        backlog_item.template_confidence = validation_result.confidence
        backlog_item.apply_refinement()

        assert backlog_item.body_markdown == refined_content
        assert backlog_item.refinement_applied is True
        assert backlog_item.detected_template == "user_story_v1"
        assert backlog_item.template_confidence == validation_result.confidence

    @beartype
    def test_refine_arbitrary_input_with_todo_markers(self, template_registry_with_defaults: TemplateRegistry) -> None:
        """Test refining arbitrary input that results in TODO markers."""
        arbitrary_issue = {
            "number": 456,
            "html_url": "https://github.com/test/repo/issues/456",
            "title": "Add feature",
            "body": "We need to add something",
            "state": "open",
        }

        backlog_item = convert_github_issue_to_backlog_item(arbitrary_issue)
        refiner = BacklogAIRefiner()
        template = template_registry_with_defaults.get_template("user_story_v1")
        assert template is not None

        # Simulate refined content with TODO markers (missing information)
        refined_content = """## As a
[TODO: specify user type]

## I want
to add something

## So that
[TODO: specify benefit]

## Acceptance Criteria
- [TODO: add criteria]"""

        validation_result = refiner.validate_and_score_refinement(
            refined_content, backlog_item.body_markdown, template, backlog_item
        )

        # Should have lower confidence due to TODO markers
        assert validation_result.confidence < 0.85
        assert validation_result.has_todo_markers is True

    @beartype
    def test_refine_arbitrary_input_with_notes_section(self, template_registry_with_defaults: TemplateRegistry) -> None:
        """Test refining arbitrary input that results in NOTES section."""
        arbitrary_issue = {
            "number": 789,
            "html_url": "https://github.com/test/repo/issues/789",
            "title": "Conflicting requirements",
            "body": """We need to implement X, but also Y.
There's some confusion about which one to prioritize.""",
            "state": "open",
        }

        backlog_item = convert_github_issue_to_backlog_item(arbitrary_issue)
        refiner = BacklogAIRefiner()
        template = template_registry_with_defaults.get_template("user_story_v1")
        assert template is not None

        # Simulate refined content with NOTES section (ambiguity detected)
        refined_content = """## As a
user

## I want
to have feature X implemented

## So that
I can accomplish my goal

## Acceptance Criteria
- Feature X is available

## NOTES
There's ambiguity about whether to prioritize X or Y.
The original request mentioned both, but they may conflict."""

        validation_result = refiner.validate_and_score_refinement(
            refined_content, backlog_item.body_markdown, template, backlog_item
        )

        # Should have lower confidence due to NOTES section
        assert validation_result.confidence < 0.85
        assert validation_result.has_notes_section is True
