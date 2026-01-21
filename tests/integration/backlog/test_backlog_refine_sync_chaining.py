"""
Integration tests for command chaining: backlog refine → sync bridge.

Tests the complete workflow where a backlog item is refined and then synced
to an external tool using the bridge sync command.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from beartype import beartype

from specfact_cli.backlog.adapters.base import BacklogAdapter
from specfact_cli.backlog.ai_refiner import BacklogAIRefiner
from specfact_cli.backlog.converter import convert_github_issue_to_backlog_item
from specfact_cli.backlog.template_detector import TemplateDetector
from specfact_cli.models.backlog_item import BacklogItem
from specfact_cli.templates.registry import TemplateRegistry


@pytest.fixture
def template_registry(tmp_path: Path) -> TemplateRegistry:
    """Create template registry with user story template."""
    registry = TemplateRegistry()

    defaults_dir = tmp_path / "templates" / "defaults"
    defaults_dir.mkdir(parents=True)

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

    registry.load_templates_from_directory(defaults_dir)
    return registry


@pytest.fixture
def mock_github_adapter() -> MagicMock:
    """Create a mock GitHub adapter that implements BacklogAdapter interface."""
    adapter = MagicMock(spec=BacklogAdapter)
    adapter.provider = "github"

    # Mock fetch_backlog_items
    def mock_fetch(items: list[dict]) -> list[BacklogItem]:
        return [convert_github_issue_to_backlog_item(item) for item in items]

    adapter.fetch_backlog_items = MagicMock(side_effect=lambda filters: mock_fetch([]))
    adapter.update_backlog_item = MagicMock(return_value=True)
    adapter.add_comment = MagicMock(return_value=True)
    return adapter


class TestBacklogRefineSyncChaining:
    """Integration tests for backlog refine → sync bridge command chaining."""

    @beartype
    def test_refine_then_sync_workflow(
        self, template_registry: TemplateRegistry, mock_github_adapter: MagicMock, tmp_path: Path
    ) -> None:
        """Test complete workflow: refine backlog item → sync to external tool."""
        # Step 1: Fetch backlog item
        github_issue = {
            "number": 123,
            "html_url": "https://github.com/org/repo/issues/123",
            "title": "We need authentication feature",
            "body": "Users want to log in. Can we add this?",
            "state": "open",
            "assignees": [{"login": "dev1"}],
            "labels": [{"name": "feature"}],
            "created_at": "2024-01-18T10:00:00Z",
            "updated_at": "2024-01-19T14:30:00Z",
        }

        backlog_item = convert_github_issue_to_backlog_item(github_issue)

        # Step 2: Detect template (simulating backlog refine command)
        detector = TemplateDetector(template_registry)
        detection_result = detector.detect_template(backlog_item)

        # If no template detected, use default user_story_v1 template
        template_id = detection_result.template_id or "user_story_v1"
        assert backlog_item.needs_refinement is True

        # Step 3: Generate refinement prompt (simulating backlog refine command)
        refiner = BacklogAIRefiner()
        template = template_registry.get_template(template_id)
        assert template is not None

        prompt = refiner.generate_refinement_prompt(backlog_item, template)
        assert backlog_item.title in prompt

        # Step 4: Simulate IDE AI copilot refinement
        refined_content = """## As a
registered user

## I want
to authenticate and log in to the system

## So that
I can access my account and protected resources

## Acceptance Criteria
- User can enter username and password
- User can click login button
- System validates credentials
- User is redirected to dashboard on successful login"""

        # Step 5: Validate refined content (simulating backlog refine command)
        validation_result = refiner.validate_and_score_refinement(refined_content, backlog_item.body_markdown, template)

        assert validation_result.confidence >= 0.85

        # Step 6: Apply refinement (simulating backlog refine command with --write)
        backlog_item.refined_body = validation_result.refined_body
        backlog_item.detected_template = template.template_id
        backlog_item.template_confidence = validation_result.confidence
        backlog_item.apply_refinement()

        assert backlog_item.body_markdown == refined_content
        assert backlog_item.refinement_applied is True

        # Step 7: Sync refined item to external tool (simulating sync bridge command)
        # This simulates: specfact sync bridge --adapter github --backlog-ids 123
        with patch("specfact_cli.adapters.registry.AdapterRegistry.get_adapter", return_value=mock_github_adapter):
            # Update the backlog item in the external tool
            success = mock_github_adapter.update_backlog_item(backlog_item)

            assert success is True
            mock_github_adapter.update_backlog_item.assert_called_once()
            call_args = mock_github_adapter.update_backlog_item.call_args[0][0]
            assert isinstance(call_args, BacklogItem)
            assert call_args.id == "123"
            assert call_args.body_markdown == refined_content
            assert call_args.refinement_applied is True

    @beartype
    def test_refine_then_sync_with_openspec_comment(
        self, template_registry: TemplateRegistry, mock_github_adapter: MagicMock, tmp_path: Path
    ) -> None:
        """Test refine → sync workflow with OpenSpec comment integration."""
        github_issue = {
            "number": 456,
            "html_url": "https://github.com/org/repo/issues/456",
            "title": "Add new feature",
            "body": "We need this feature",
            "state": "open",
        }

        backlog_item = convert_github_issue_to_backlog_item(github_issue)

        # Refine the item
        detector = TemplateDetector(template_registry)
        detection_result = detector.detect_template(backlog_item)
        template_id = detection_result.template_id or "user_story_v1"
        template = template_registry.get_template(template_id)
        assert template is not None

        refiner = BacklogAIRefiner()
        refined_content = """## As a
user

## I want
this feature

## So that
I can accomplish my goal

## Acceptance Criteria
- Feature is available"""

        validation_result = refiner.validate_and_score_refinement(refined_content, backlog_item.body_markdown, template)
        backlog_item.refined_body = validation_result.refined_body
        backlog_item.apply_refinement()

        # Simulate sync bridge with OpenSpec comment (--openspec-comment flag)
        # This simulates: specfact sync bridge --adapter github --backlog-ids 456 --openspec-comment
        openspec_comment = (
            "OpenSpec change proposal: add-new-feature\nSee: https://openspec.example.com/changes/add-new-feature"
        )

        with patch("specfact_cli.adapters.registry.AdapterRegistry.get_adapter", return_value=mock_github_adapter):
            # Update backlog item
            mock_github_adapter.update_backlog_item(backlog_item)

            # Add OpenSpec comment (preserving original body)
            mock_github_adapter.add_comment(backlog_item.id, openspec_comment)

            # Verify both operations were called
            mock_github_adapter.update_backlog_item.assert_called_once()
            mock_github_adapter.add_comment.assert_called_once_with(backlog_item.id, openspec_comment)

    @beartype
    def test_refine_then_sync_cross_adapter(self, template_registry: TemplateRegistry, tmp_path: Path) -> None:
        """Test refine from GitHub → sync to ADO (cross-adapter sync)."""
        # Step 1: Refine GitHub issue
        github_issue = {
            "number": 789,
            "html_url": "https://github.com/org/repo/issues/789",
            "title": "User Story: Improve performance",
            "body": "The app is slow. We need to optimize it.",
            "state": "open",
        }

        backlog_item = convert_github_issue_to_backlog_item(github_issue)

        # Refine using template
        detector = TemplateDetector(template_registry)
        detection_result = detector.detect_template(backlog_item)
        template_id = detection_result.template_id or "user_story_v1"
        template = template_registry.get_template(template_id)
        assert template is not None

        refiner = BacklogAIRefiner()
        refined_content = """## As a
user

## I want
faster application performance

## So that
I can complete my tasks without delays

## Acceptance Criteria
- Page load time < 2 seconds
- API response time < 500ms"""

        validation_result = refiner.validate_and_score_refinement(refined_content, backlog_item.body_markdown, template)
        backlog_item.refined_body = validation_result.refined_body
        backlog_item.apply_refinement()

        # Step 2: Create mock ADO adapter for cross-adapter sync
        mock_ado_adapter = MagicMock(spec=BacklogAdapter)
        mock_ado_adapter.provider = "ado"
        mock_ado_adapter.update_backlog_item = MagicMock(return_value=True)

        # Step 3: Sync to ADO (simulating: specfact sync bridge --adapter ado --backlog-ids 789)
        with patch("specfact_cli.adapters.registry.AdapterRegistry.get_adapter", return_value=mock_ado_adapter):
            success = mock_ado_adapter.update_backlog_item(backlog_item)

            assert success is True
            mock_ado_adapter.update_backlog_item.assert_called_once()

            # Verify the refined content is preserved in cross-adapter sync
            call_args = mock_ado_adapter.update_backlog_item.call_args[0][0]
            assert call_args.body_markdown == refined_content
            assert call_args.refinement_applied is True
            # Original provider info should be preserved
            assert call_args.provider == "github"
            assert call_args.id == "789"
