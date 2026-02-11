"""
Unit tests for BacklogAIRefiner.

Tests prompt generation and refinement validation.
"""

from __future__ import annotations

import pytest
from beartype import beartype

from specfact_cli.backlog.ai_refiner import BacklogAIRefiner, RefinementResult
from specfact_cli.models.backlog_item import BacklogItem
from specfact_cli.templates.registry import BacklogTemplate


@pytest.fixture
def refiner() -> BacklogAIRefiner:
    """Create BacklogAIRefiner instance."""
    return BacklogAIRefiner()


@pytest.fixture
def user_story_template() -> BacklogTemplate:
    """Create user story template for testing."""
    return BacklogTemplate(
        template_id="user_story_v1",
        name="User Story",
        description="Standard user story template",
        required_sections=["As a", "I want", "So that", "Acceptance Criteria"],
        optional_sections=["Notes"],
        body_patterns={"as_a": "As a [^,]+ I want"},
    )


@pytest.fixture
def arbitrary_backlog_item() -> BacklogItem:
    """Create arbitrary backlog item (typical DevOps input)."""
    return BacklogItem(
        id="123",
        provider="github",
        url="https://github.com/test/repo/issues/123",
        title="Need to add login feature",
        body_markdown="""Hey team,
We need to add a login feature. Users are asking for it.
Can someone implement this?

Thanks!""",
        state="open",
    )


class TestBacklogAIRefiner:
    """Test BacklogAIRefiner."""

    @beartype
    def test_generate_refinement_prompt(
        self, refiner: BacklogAIRefiner, arbitrary_backlog_item: BacklogItem, user_story_template: BacklogTemplate
    ) -> None:
        """Test generating refinement prompt for IDE AI copilot."""
        prompt = refiner.generate_refinement_prompt(arbitrary_backlog_item, user_story_template)

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert arbitrary_backlog_item.title in prompt
        assert arbitrary_backlog_item.body_markdown in prompt
        assert user_story_template.name in prompt
        assert "As a" in prompt
        assert "I want" in prompt

    @beartype
    def test_generate_refinement_prompt_includes_comments_when_provided(
        self, refiner: BacklogAIRefiner, arbitrary_backlog_item: BacklogItem, user_story_template: BacklogTemplate
    ) -> None:
        """Prompt includes comment context so refinement sees evolving discussion."""
        prompt = refiner.generate_refinement_prompt(
            arbitrary_backlog_item,
            user_story_template,
            comments=["First update from team", "Final clarification from PO"],
        )
        assert "Comments" in prompt
        assert "First update from team" in prompt
        assert "Final clarification from PO" in prompt

    @beartype
    def test_generate_refinement_prompt_mentions_no_comments_when_empty(
        self, refiner: BacklogAIRefiner, arbitrary_backlog_item: BacklogItem, user_story_template: BacklogTemplate
    ) -> None:
        """Prompt explicitly states that comments were checked but none exist."""
        prompt = refiner.generate_refinement_prompt(arbitrary_backlog_item, user_story_template, comments=[])
        assert "No comments found" in prompt

    @beartype
    def test_validate_and_score_complete_refinement(
        self, refiner: BacklogAIRefiner, arbitrary_backlog_item: BacklogItem, user_story_template: BacklogTemplate
    ) -> None:
        """Test validating complete refinement (high confidence)."""
        original_body = "Some original content"
        refined_body = """## As a
user

## I want
to log in

## So that
I can access my account

## Acceptance Criteria
- User can enter credentials
- User can click login button"""

        result = refiner.validate_and_score_refinement(
            refined_body, original_body, user_story_template, arbitrary_backlog_item
        )

        assert isinstance(result, RefinementResult)
        assert result.refined_body == refined_body
        assert result.confidence >= 0.85
        assert result.has_todo_markers is False
        assert result.has_notes_section is False

    @beartype
    def test_validate_and_score_with_todo_markers(
        self, refiner: BacklogAIRefiner, arbitrary_backlog_item: BacklogItem, user_story_template: BacklogTemplate
    ) -> None:
        """Test validating refinement with TODO markers (medium confidence)."""
        original_body = "Some original content"
        refined_body = """## As a
user

## I want
to log in

## So that
[TODO: specify the benefit]

## Acceptance Criteria
- User can enter credentials
- [TODO: add more criteria]"""

        result = refiner.validate_and_score_refinement(
            refined_body, original_body, user_story_template, arbitrary_backlog_item
        )

        assert result.confidence < 0.85
        assert result.has_todo_markers is True

    @beartype
    def test_validate_and_score_with_notes_section(
        self, refiner: BacklogAIRefiner, arbitrary_backlog_item: BacklogItem, user_story_template: BacklogTemplate
    ) -> None:
        """Test validating refinement with NOTES section (lower confidence)."""
        original_body = "Some original content"
        refined_body = """## As a
user

## I want
to log in

## So that
I can access my account

## Acceptance Criteria
- User can enter credentials

## NOTES
There's some ambiguity about the login method."""

        result = refiner.validate_and_score_refinement(
            refined_body, original_body, user_story_template, arbitrary_backlog_item
        )

        assert result.confidence < 0.85
        assert result.has_notes_section is True

    @beartype
    def test_validate_missing_required_sections_raises(
        self, refiner: BacklogAIRefiner, arbitrary_backlog_item: BacklogItem, user_story_template: BacklogTemplate
    ) -> None:
        """Test that validation raises error for missing required sections."""
        original_body = "Some original content"
        refined_body = "Incomplete refinement without required sections"

        with pytest.raises(ValueError, match="missing required sections"):
            refiner.validate_and_score_refinement(
                refined_body, original_body, user_story_template, arbitrary_backlog_item
            )

    @beartype
    def test_validate_empty_refinement_raises(
        self, refiner: BacklogAIRefiner, arbitrary_backlog_item: BacklogItem, user_story_template: BacklogTemplate
    ) -> None:
        """Test that validation raises error for empty refinement."""
        original_body = "Some original content"
        refined_body = ""

        with pytest.raises(ValueError, match="Refined body is empty"):
            refiner.validate_and_score_refinement(
                refined_body, original_body, user_story_template, arbitrary_backlog_item
            )

    @beartype
    def test_validate_arbitrary_input_refinement(
        self, refiner: BacklogAIRefiner, arbitrary_backlog_item: BacklogItem, user_story_template: BacklogTemplate
    ) -> None:
        """Test validating refinement of arbitrary DevOps input."""
        # Simulate refined content from IDE AI copilot
        refined_body = """## As a
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

        result = refiner.validate_and_score_refinement(
            refined_body, arbitrary_backlog_item.body_markdown, user_story_template, arbitrary_backlog_item
        )

        assert result.confidence >= 0.85
        assert all(section in result.refined_body for section in ["As a", "I want", "So that", "Acceptance Criteria"])

    @beartype
    def test_validate_agile_fields_valid(self, refiner: BacklogAIRefiner) -> None:
        """Test validating agile fields with valid values."""
        item = BacklogItem(
            id="123",
            provider="github",
            url="https://github.com/test/repo/issues/123",
            title="Test",
            body_markdown="Test",
            state="open",
            story_points=8,
            business_value=50,
            priority=2,
            value_points=6,
        )

        errors = refiner._validate_agile_fields(item)
        assert errors == []

    @beartype
    def test_validate_agile_fields_invalid_story_points(self, refiner: BacklogAIRefiner) -> None:
        """Test validating agile fields with invalid story_points."""
        item = BacklogItem(
            id="123",
            provider="github",
            url="https://github.com/test/repo/issues/123",
            title="Test",
            body_markdown="Test",
            state="open",
            story_points=150,  # Out of range
        )

        errors = refiner._validate_agile_fields(item)
        assert len(errors) > 0
        assert any("story_points" in error and "0-100" in error for error in errors)

    @beartype
    def test_validate_agile_fields_invalid_priority(self, refiner: BacklogAIRefiner) -> None:
        """Test validating agile fields with invalid priority."""
        item = BacklogItem(
            id="123",
            provider="github",
            url="https://github.com/test/repo/issues/123",
            title="Test",
            body_markdown="Test",
            state="open",
            priority=10,  # Out of range
        )

        errors = refiner._validate_agile_fields(item)
        assert len(errors) > 0
        assert any("priority" in error and "1-4" in error for error in errors)

    @beartype
    def test_validate_and_score_with_invalid_fields_raises(
        self, refiner: BacklogAIRefiner, arbitrary_backlog_item: BacklogItem, user_story_template: BacklogTemplate
    ) -> None:
        """Test that validation raises error for invalid agile fields."""
        # Create item with invalid story_points
        invalid_item = BacklogItem(
            id="123",
            provider="github",
            url="https://github.com/test/repo/issues/123",
            title="Test",
            body_markdown="Test",
            state="open",
            story_points=150,  # Out of range
        )

        original_body = "Some original content"
        refined_body = """## As a
user

## I want
to log in

## So that
I can access my account

## Acceptance Criteria
- User can enter credentials"""

        with pytest.raises(ValueError, match="Field validation errors"):
            refiner.validate_and_score_refinement(refined_body, original_body, user_story_template, invalid_item)
