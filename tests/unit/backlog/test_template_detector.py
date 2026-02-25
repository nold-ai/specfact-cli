"""
Unit tests for TemplateDetector.

Tests template detection with various backlog item formats and confidence scoring.
"""

from __future__ import annotations

import pytest
from beartype import beartype

from specfact_cli.backlog.template_detector import TemplateDetector, get_effective_required_sections
from specfact_cli.models.backlog_item import BacklogItem
from specfact_cli.templates.registry import BacklogTemplate, TemplateRegistry


@pytest.fixture
def template_registry() -> TemplateRegistry:
    """Create template registry with test templates."""
    registry = TemplateRegistry()

    # User story template
    user_story = BacklogTemplate(
        template_id="user_story_v1",
        name="User Story",
        required_sections=["As a", "I want", "So that", "Acceptance Criteria"],
        body_patterns={"as_a": "As a [^,]+ I want"},
        title_patterns=["^.*[Uu]ser [Ss]tory.*$"],
    )
    registry.register_template(user_story)

    # Defect template
    defect = BacklogTemplate(
        template_id="defect_v1",
        name="Defect",
        required_sections=["Description", "Steps to Reproduce", "Expected Behavior", "Actual Behavior"],
        body_patterns={"steps": "[Ss]teps? to [Rr]eproduce"},
        title_patterns=["^.*[Bb]ug.*$"],
    )
    registry.register_template(defect)

    return registry


@pytest.fixture
def detector(template_registry: TemplateRegistry) -> TemplateDetector:
    """Create template detector with test registry."""
    return TemplateDetector(template_registry)


class TestTemplateDetector:
    """Test TemplateDetector."""

    @beartype
    def test_detect_high_confidence_match(self, detector: TemplateDetector) -> None:
        """Test detecting template with high confidence."""
        item = BacklogItem(
            id="1",
            provider="github",
            url="https://github.com/test/repo/issues/1",
            title="User Story: Add login feature",
            body_markdown="""## As a
user

## I want
to log in

## So that
I can access my account

## Acceptance Criteria
- User can enter credentials
- User can click login button""",
            state="open",
        )

        result = detector.detect_template(item)

        assert result.template_id == "user_story_v1"
        assert result.confidence >= 0.8
        assert len(result.missing_fields) == 0

    @beartype
    def test_detect_medium_confidence_match(self, detector: TemplateDetector) -> None:
        """Test detecting template with medium confidence (missing some sections)."""
        item = BacklogItem(
            id="2",
            provider="github",
            url="https://github.com/test/repo/issues/2",
            title="User Story: Add feature",
            body_markdown="""## As a
user

## I want
to do something""",
            state="open",
        )

        result = detector.detect_template(item)

        assert result.template_id == "user_story_v1"
        assert 0.5 <= result.confidence < 0.8
        assert len(result.missing_fields) > 0

    @beartype
    def test_detect_no_match(self, detector: TemplateDetector) -> None:
        """Test detecting no template match."""
        item = BacklogItem(
            id="3",
            provider="github",
            url="https://github.com/test/repo/issues/3",
            title="Random issue",
            body_markdown="Some random content without structure",
            state="open",
        )

        result = detector.detect_template(item)

        assert result.template_id is None
        assert result.confidence < 0.5

    @beartype
    def test_detect_defect_template(self, detector: TemplateDetector) -> None:
        """Test detecting defect template."""
        item = BacklogItem(
            id="4",
            provider="github",
            url="https://github.com/test/repo/issues/4",
            title="Bug: Login fails",
            body_markdown="""## Description
Login doesn't work

## Steps to Reproduce
1. Go to login page
2. Enter credentials
3. Click login

## Expected Behavior
User should be logged in

## Actual Behavior
Error message appears""",
            state="open",
        )

        result = detector.detect_template(item)

        assert result.template_id == "defect_v1"
        assert result.confidence >= 0.8

    @beartype
    def test_detect_with_pattern_match(self, detector: TemplateDetector) -> None:
        """Test detection with pattern matching."""
        item = BacklogItem(
            id="5",
            provider="github",
            url="https://github.com/test/repo/issues/5",
            title="User Story: Feature X",
            body_markdown="As a developer I want to add features",
            state="open",
        )

        result = detector.detect_template(item)

        # Should match user story based on title pattern and body pattern
        assert result.template_id == "user_story_v1"
        assert result.confidence > 0.0

    @beartype
    def test_detect_arbitrary_input(self, detector: TemplateDetector) -> None:
        """Test detection with arbitrary DevOps backlog input."""
        # Simulate arbitrary input that DevOps team might put in
        item = BacklogItem(
            id="6",
            provider="github",
            url="https://github.com/test/repo/issues/6",
            title="Need to fix the thing",
            body_markdown="""Hey team,
We need to fix this issue. It's been reported by users.
Can someone look into it?

Thanks!""",
            state="open",
        )

        result = detector.detect_template(item)

        # Should not match any template (low or no confidence)
        assert result.confidence < 0.5

    @beartype
    def test_detect_with_persona_framework_provider_filtering(self, template_registry: TemplateRegistry) -> None:
        """Test template detection with persona/framework/provider filtering."""
        # Add framework-specific template
        scrum_template = BacklogTemplate(
            template_id="scrum_story_v1",
            name="Scrum User Story",
            framework="scrum",
            required_sections=["As a", "I want"],
            body_patterns={"as_a": "As a [^,]+ I want"},
        )
        template_registry.register_template(scrum_template)

        detector = TemplateDetector(template_registry)

        item = BacklogItem(
            id="7",
            provider="github",
            url="https://github.com/test/repo/issues/7",
            title="User Story: Add feature",
            body_markdown="""## As a
user

## I want
to add features""",
            state="open",
        )

        # Test with framework filter
        result = detector.detect_template(item, provider="github", framework="scrum")
        assert result.template_id == "scrum_story_v1"

        # Test without framework filter (should match default)
        result = detector.detect_template(item, provider="github", framework=None)
        assert result.template_id in ["user_story_v1", "scrum_story_v1"]  # Either could match

    @beartype
    def test_ado_effective_required_sections_ignores_structured_metric_sections(self) -> None:
        """ADO should not require structured metric sections in markdown body."""
        template = BacklogTemplate(
            template_id="scrum_user_story_v1",
            name="Scrum User Story",
            required_sections=["As a", "I want", "So that", "Acceptance Criteria", "Story Points"],
        )
        item = BacklogItem(
            id="8",
            provider="ado",
            url="https://dev.azure.com/org/project/_workitems/edit/8",
            title="User Story",
            body_markdown="## As a\nuser\n\n## I want\nvalue\n\n## So that\nbenefit\n\n## Acceptance Criteria\n- [ ] done",
            state="Active",
        )
        effective = get_effective_required_sections(item, template)
        assert "Story Points" not in effective
        assert "Acceptance Criteria" in effective
