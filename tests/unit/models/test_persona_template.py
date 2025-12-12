"""Unit tests for PersonaTemplate models."""

import pytest

from specfact_cli.models.persona_template import (
    PersonaTemplate,
    SectionType,
    SectionValidation,
    TemplateSection,
)


class TestTemplateSection:
    """Test suite for TemplateSection model."""

    def test_create_section(self) -> None:
        """Test creating a template section."""
        section = TemplateSection(
            name="test_section",
            heading="## Test Section",
            type=SectionType.REQUIRED,
            description="Test description",
            order=1,
            validation=None,
            placeholder=None,
            condition=None,
        )

        assert section.name == "test_section"
        assert section.heading == "## Test Section"
        assert section.type == SectionType.REQUIRED
        assert section.order == 1

    def test_section_optional_fields(self) -> None:
        """Test template section with optional fields."""
        validation = SectionValidation(min_items=1, max_items=10, pattern=None, required_fields=[], format=None)
        section = TemplateSection(
            name="test_section",
            heading="## Test Section",
            type=SectionType.OPTIONAL,
            description="Test description",
            order=1,
            validation=validation,
            placeholder="*[ACTION REQUIRED]*",
            condition="if features exist",
        )

        assert section.validation == validation
        assert section.placeholder == "*[ACTION REQUIRED]*"
        assert section.condition == "if features exist"


class TestPersonaTemplate:
    """Test suite for PersonaTemplate model."""

    @pytest.fixture
    def sample_template(self) -> PersonaTemplate:
        """Create a sample persona template."""
        sections = [
            TemplateSection(
                name="idea",
                heading="## Idea & Business Context",
                type=SectionType.REQUIRED,
                description="Problem statement",
                order=1,
                validation=None,
                placeholder=None,
                condition=None,
            ),
            TemplateSection(
                name="features",
                heading="## Features",
                type=SectionType.REQUIRED,
                description="Features",
                order=2,
                validation=None,
                placeholder=None,
                condition=None,
            ),
            TemplateSection(
                name="notes",
                heading="## Notes",
                type=SectionType.OPTIONAL,
                description="Additional notes",
                order=3,
                validation=None,
                placeholder=None,
                condition=None,
            ),
        ]
        return PersonaTemplate(
            persona_name="product-owner",
            version="1.0.0",
            description="Template for product owner",
            sections=sections,
        )

    def test_get_required_sections(self, sample_template: PersonaTemplate) -> None:
        """Test getting required sections."""
        required = sample_template.get_required_sections()

        assert isinstance(required, list)
        assert "idea" in required
        assert "features" in required
        assert "notes" not in required  # Optional section

    def test_get_section_order(self, sample_template: PersonaTemplate) -> None:
        """Test getting section order."""
        order = sample_template.get_section_order()

        assert isinstance(order, list)
        assert len(order) == 3
        assert order[0] == "idea"  # order=1
        assert order[1] == "features"  # order=2
        assert order[2] == "notes"  # order=3

    def test_get_section(self, sample_template: PersonaTemplate) -> None:
        """Test getting section by name."""
        section = sample_template.get_section("idea")

        assert section is not None
        assert section.name == "idea"
        assert section.heading == "## Idea & Business Context"

    def test_get_section_not_found(self, sample_template: PersonaTemplate) -> None:
        """Test getting non-existent section returns None."""
        section = sample_template.get_section("nonexistent")

        assert section is None

    def test_is_required(self, sample_template: PersonaTemplate) -> None:
        """Test checking if section is required."""
        assert sample_template.is_required("idea") is True
        assert sample_template.is_required("features") is True
        assert sample_template.is_required("notes") is False
        assert sample_template.is_required("nonexistent") is False


class TestSectionValidation:
    """Test suite for SectionValidation model."""

    def test_create_validation(self) -> None:
        """Test creating section validation."""
        validation = SectionValidation(
            min_items=1,
            max_items=10,
            pattern=r"^[A-Z]+-\d+$",
            required_fields=["title", "description"],
            format="checklist",
        )

        assert validation.min_items == 1
        assert validation.max_items == 10
        assert validation.pattern == r"^[A-Z]+-\d+$"
        assert "title" in validation.required_fields
        assert validation.format == "checklist"

    def test_validation_optional_fields(self) -> None:
        """Test validation with optional fields."""
        validation = SectionValidation(min_items=None, max_items=None, pattern=None, required_fields=[], format=None)

        assert validation.min_items is None
        assert validation.max_items is None
        assert validation.pattern is None
        assert validation.required_fields == []
        assert validation.format is None
