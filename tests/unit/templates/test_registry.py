"""
Unit tests for TemplateRegistry.

Tests template registration, retrieval, listing, and YAML loading.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from beartype import beartype

from specfact_cli.templates.registry import BacklogTemplate, TemplateRegistry


class TestBacklogTemplate:
    """Test BacklogTemplate model."""

    @beartype
    def test_create_template_minimal(self) -> None:
        """Test creating template with minimal fields."""
        template = BacklogTemplate(
            template_id="test_v1",
            name="Test Template",
        )

        assert template.template_id == "test_v1"
        assert template.name == "Test Template"
        assert template.scope == "corporate"
        assert template.required_sections == []
        assert template.optional_sections == []

    @beartype
    def test_create_template_full(self) -> None:
        """Test creating template with all fields."""
        template = BacklogTemplate(
            template_id="user_story_v1",
            name="User Story",
            description="Standard user story template",
            scope="corporate",
            personas=["product-owner"],
            framework="scrum",
            provider="github",
            required_sections=["As a", "I want", "So that"],
            optional_sections=["Notes"],
            body_patterns={"as_a": "As a [^,]+ I want"},
            title_patterns=["^.*[Uu]ser [Ss]tory.*$"],
            schema_ref="openspec/templates/user_story_v1/",
        )

        assert template.template_id == "user_story_v1"
        assert template.name == "User Story"
        assert template.personas == ["product-owner"]
        assert template.framework == "scrum"
        assert template.provider == "github"
        assert len(template.required_sections) == 3
        assert len(template.body_patterns) == 1

    @beartype
    def test_create_template_with_personas_framework_provider(self) -> None:
        """Test creating template with personas, framework, and provider fields."""
        template = BacklogTemplate(
            template_id="scrum_story_v1",
            name="Scrum User Story",
            personas=["product-owner", "developer"],
            framework="scrum",
            provider="ado",
        )

        assert template.personas == ["product-owner", "developer"]
        assert template.framework == "scrum"
        assert template.provider == "ado"
        assert template.scope == "corporate"  # Default

    @beartype
    def test_resolve_template_priority_based(self) -> None:
        """Test priority-based template resolution."""
        registry = TemplateRegistry()

        # Default template (no filters)
        default_template = BacklogTemplate(template_id="default_v1", name="Default")
        registry.register_template(default_template)

        # Framework-specific template
        scrum_template = BacklogTemplate(template_id="scrum_v1", name="Scrum", framework="scrum")
        registry.register_template(scrum_template)

        # Provider-specific template
        github_template = BacklogTemplate(template_id="github_v1", name="GitHub", provider="github")
        registry.register_template(github_template)

        # Provider+framework template (most specific)
        scrum_github_template = BacklogTemplate(
            template_id="scrum_github_v1", name="Scrum GitHub", framework="scrum", provider="github"
        )
        registry.register_template(scrum_github_template)

        # Test priority-based resolution
        # Most specific: provider+framework
        result = registry.resolve_template(provider="github", framework="scrum")
        assert result is not None
        assert result.template_id == "scrum_github_v1"

        # Framework only
        result = registry.resolve_template(provider=None, framework="scrum")
        assert result is not None
        assert result.template_id == "scrum_v1"

        # Provider only
        result = registry.resolve_template(provider="github", framework=None)
        assert result is not None
        assert result.template_id == "github_v1"

        # Default (no filters)
        result = registry.resolve_template(provider=None, framework=None)
        assert result is not None
        assert result.template_id == "default_v1"

    @beartype
    def test_resolve_template_with_persona(self) -> None:
        """Test template resolution with persona filter."""
        registry = TemplateRegistry()

        # Persona-specific template
        po_template = BacklogTemplate(template_id="po_v1", name="Product Owner", personas=["product-owner"])
        registry.register_template(po_template)

        # Default template (no persona)
        default_template = BacklogTemplate(template_id="default_v1", name="Default")
        registry.register_template(default_template)

        # Test persona resolution
        result = registry.resolve_template(persona="product-owner")
        assert result is not None
        assert result.template_id == "po_v1"

        # No persona - should get default
        result = registry.resolve_template(persona=None)
        assert result is not None
        assert result.template_id == "default_v1"


class TestTemplateRegistry:
    """Test TemplateRegistry."""

    @beartype
    def test_register_template(self) -> None:
        """Test registering a template."""
        registry = TemplateRegistry()
        template = BacklogTemplate(template_id="test_v1", name="Test Template")

        registry.register_template(template)

        assert registry.get_template("test_v1") == template

    @beartype
    def test_get_template_not_found(self) -> None:
        """Test getting non-existent template returns None."""
        registry = TemplateRegistry()

        assert registry.get_template("nonexistent") is None

    @beartype
    def test_list_templates_corporate(self) -> None:
        """Test listing corporate templates."""
        registry = TemplateRegistry()
        corporate_template = BacklogTemplate(template_id="corp_v1", name="Corporate", scope="corporate")
        team_template = BacklogTemplate(template_id="team_v1", name="Team", scope="team", team_id="team1")

        registry.register_template(corporate_template)
        registry.register_template(team_template)

        templates = registry.list_templates(scope="corporate")

        assert len(templates) == 1
        assert templates[0].template_id == "corp_v1"

    @beartype
    def test_list_templates_team(self) -> None:
        """Test listing team-scoped templates."""
        registry = TemplateRegistry()
        team1_template = BacklogTemplate(template_id="team1_v1", name="Team1", scope="team", team_id="team1")
        team2_template = BacklogTemplate(template_id="team2_v1", name="Team2", scope="team", team_id="team2")

        registry.register_template(team1_template)
        registry.register_template(team2_template)

        templates = registry.list_templates(scope="team", team_id="team1")

        assert len(templates) == 1
        assert templates[0].template_id == "team1_v1"

    @beartype
    def test_load_template_from_file(self, tmp_path: Path) -> None:
        """Test loading template from YAML file."""
        template_file = tmp_path / "template.yaml"
        template_data = {
            "template_id": "test_v1",
            "name": "Test Template",
            "description": "Test description",
            "scope": "corporate",
            "personas": ["product-owner"],
            "framework": "scrum",
            "provider": "github",
            "required_sections": ["Section1", "Section2"],
            "optional_sections": ["Notes"],
            "body_patterns": {"pattern1": "regex1"},
            "title_patterns": ["^test.*$"],
        }
        template_file.write_text(yaml.dump(template_data))

        registry = TemplateRegistry()
        registry.load_template_from_file(template_file)

        template = registry.get_template("test_v1")
        assert template is not None
        assert template.name == "Test Template"
        assert template.personas == ["product-owner"]
        assert template.framework == "scrum"
        assert template.provider == "github"
        assert len(template.required_sections) == 2

    @beartype
    def test_load_template_from_directory(self, tmp_path: Path) -> None:
        """Test loading templates from directory."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        # Create two template files
        template1_file = template_dir / "template1.yaml"
        template1_file.write_text(yaml.dump({"template_id": "template1", "name": "Template 1", "scope": "corporate"}))

        template2_file = template_dir / "template2.yaml"
        template2_file.write_text(yaml.dump({"template_id": "template2", "name": "Template 2", "scope": "corporate"}))

        registry = TemplateRegistry()
        registry.load_templates_from_directory(template_dir)

        assert registry.get_template("template1") is not None
        assert registry.get_template("template2") is not None

    @beartype
    def test_load_template_file_not_found(self) -> None:
        """Test loading non-existent template file raises error."""
        registry = TemplateRegistry()
        non_existent = Path("/nonexistent/template.yaml")

        with pytest.raises(FileNotFoundError):
            registry.load_template_from_file(non_existent)
