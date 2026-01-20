"""
Template registry for backlog item templates.

This module provides centralized template management with detection, matching,
and scoping capabilities (corporate, team, user).
"""

from __future__ import annotations

from pathlib import Path

from beartype import beartype
from icontract import ensure, require
from pydantic import BaseModel, Field


class BacklogTemplate(BaseModel):
    """
    Backlog template definition.

    Templates define the structure and patterns for backlog items (user stories,
    defects, spikes, enablers) with required sections, optional sections,
    regex patterns, and OpenSpec schema references.
    """

    template_id: str = Field(..., description="Unique template identifier (e.g., 'user_story_v1')")
    name: str = Field(..., description="Human-readable template name")
    description: str = Field(default="", description="Template description")
    scope: str = Field(default="corporate", description="Template scope: corporate, team, or user")
    team_id: str | None = Field(default=None, description="Team ID for team-scoped templates")
    personas: list[str] = Field(
        default_factory=list,
        description="Personas this template applies to (product-owner, architect, developer). Empty = all personas",
    )
    framework: str | None = Field(
        default=None,
        description="Framework this template is for (agile, scrum, safe, kanban). None = framework-agnostic",
    )
    provider: str | None = Field(
        default=None,
        description="Provider this template is optimized for (github, ado, jira, linear). None = provider-agnostic",
    )
    required_sections: list[str] = Field(
        default_factory=list, description="List of required section headings (e.g., 'As a', 'I want')"
    )
    optional_sections: list[str] = Field(default_factory=list, description="List of optional section headings")
    body_patterns: dict[str, str] = Field(
        default_factory=dict,
        description="Regex patterns for body content matching (e.g., {'as_a': 'As a [^,]+ I want'})",
    )
    title_patterns: list[str] = Field(default_factory=list, description="Regex patterns for title matching")
    schema_ref: str | None = Field(
        default=None, description="OpenSpec schema reference (e.g., 'openspec/templates/user_story_v1/')"
    )


class TemplateRegistry:
    """
    Centralized template registry with detection, matching, and scoping.

    The registry manages backlog templates with support for:
    - Corporate templates (available to all teams)
    - Team-specific templates (scoped to specific teams)
    - User-specific templates (scoped to individual users)
    """

    def __init__(self) -> None:
        """Initialize template registry."""
        self._templates: dict[str, BacklogTemplate] = {}

    @beartype
    @require(lambda self, template: isinstance(template, BacklogTemplate), "Template must be BacklogTemplate")
    @ensure(lambda result: result is None, "Must return None")
    def register_template(self, template: BacklogTemplate) -> None:
        """
        Register a template in the registry.

        Args:
            template: BacklogTemplate instance to register
        """
        self._templates[template.template_id] = template

    @beartype
    @require(
        lambda self, template_id: isinstance(template_id, str) and len(template_id) > 0, "Template ID must be non-empty"
    )
    @ensure(lambda result: result is None or isinstance(result, BacklogTemplate), "Must return BacklogTemplate or None")
    def get_template(self, template_id: str) -> BacklogTemplate | None:
        """
        Get template by ID.

        Args:
            template_id: Template identifier

        Returns:
            BacklogTemplate if found, None otherwise
        """
        return self._templates.get(template_id)

    @beartype
    @require(lambda self, scope: scope in ("corporate", "team", "user"), "Scope must be corporate, team, or user")
    @require(lambda self, team_id: team_id is None or isinstance(team_id, str), "Team ID must be str or None")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def list_templates(self, scope: str = "corporate", team_id: str | None = None) -> list[BacklogTemplate]:
        """
        List templates matching the requested scope.

        Args:
            scope: Template scope (corporate, team, or user)
            team_id: Team ID for team-scoped templates (required if scope is 'team')

        Returns:
            List of BacklogTemplate instances matching the scope
        """
        templates: list[BacklogTemplate] = []
        for template in self._templates.values():
            if template.scope == "corporate" or (template.scope == "team" and team_id and template.team_id == team_id):
                templates.append(template)
            elif template.scope == "user":
                # User templates are handled separately (not implemented in this version)
                pass
        return templates

    @beartype
    @require(lambda self, template_path: isinstance(template_path, Path), "Template path must be Path")
    @ensure(lambda result: result is None, "Must return None")
    def load_template_from_file(self, template_path: Path) -> None:
        """
        Load template from YAML file.

        Args:
            template_path: Path to template YAML file

        Raises:
            FileNotFoundError: If template file doesn't exist
            ValueError: If template file is malformed
        """
        if not template_path.exists():
            msg = f"Template file not found: {template_path}"
            raise FileNotFoundError(msg)

        # Import yaml here to avoid circular dependencies
        import yaml

        try:
            with template_path.open() as f:
                data = yaml.safe_load(f)
                if not isinstance(data, dict):
                    msg = f"Template file must contain a YAML dict: {template_path}"
                    raise ValueError(msg)

                template = BacklogTemplate(
                    template_id=data.get("template_id", template_path.stem),
                    name=data.get("name", ""),
                    description=data.get("description", ""),
                    scope=data.get("scope", "corporate"),
                    team_id=data.get("team_id"),
                    personas=data.get("personas", []),
                    framework=data.get("framework"),
                    provider=data.get("provider"),
                    required_sections=data.get("required_sections", []),
                    optional_sections=data.get("optional_sections", []),
                    body_patterns=data.get("body_patterns", {}),
                    title_patterns=data.get("title_patterns", []),
                    schema_ref=data.get("schema_ref"),
                )
                self.register_template(template)
        except yaml.YAMLError as e:
            msg = f"Failed to parse template YAML: {template_path}: {e}"
            raise ValueError(msg) from e

    @beartype
    @require(lambda self, template_dir: isinstance(template_dir, Path), "Template directory must be Path")
    @ensure(lambda result: result is None, "Must return None")
    def load_templates_from_directory(self, template_dir: Path) -> None:
        """
        Load all templates from a directory (including subdirectories for frameworks/, personas/, providers/).

        Args:
            template_dir: Directory containing template YAML files

        Raises:
            FileNotFoundError: If template directory doesn't exist
        """
        if not template_dir.exists():
            msg = f"Template directory not found: {template_dir}"
            raise FileNotFoundError(msg)

        # Load templates from defaults/ subdirectory (if it exists)
        defaults_dir = template_dir / "defaults"
        if defaults_dir.exists():
            for template_file in defaults_dir.glob("*.yaml"):
                self.load_template_from_file(template_file)
            for template_file in defaults_dir.glob("*.yml"):
                self.load_template_from_file(template_file)
        else:
            # Fallback: Load templates directly from directory root (for backward compatibility)
            for template_file in template_dir.glob("*.yaml"):
                self.load_template_from_file(template_file)
            for template_file in template_dir.glob("*.yml"):
                self.load_template_from_file(template_file)

        # Load templates from frameworks/ subdirectory
        frameworks_dir = template_dir / "frameworks"
        if frameworks_dir.exists():
            for framework_dir in frameworks_dir.iterdir():
                if framework_dir.is_dir():
                    for template_file in framework_dir.glob("*.yaml"):
                        self.load_template_from_file(template_file)
                    for template_file in framework_dir.glob("*.yml"):
                        self.load_template_from_file(template_file)

        # Load templates from personas/ subdirectory
        personas_dir = template_dir / "personas"
        if personas_dir.exists():
            for persona_dir in personas_dir.iterdir():
                if persona_dir.is_dir():
                    for template_file in persona_dir.glob("*.yaml"):
                        self.load_template_from_file(template_file)
                    for template_file in persona_dir.glob("*.yml"):
                        self.load_template_from_file(template_file)

        # Load templates from providers/ subdirectory
        providers_dir = template_dir / "providers"
        if providers_dir.exists():
            for provider_dir in providers_dir.iterdir():
                if provider_dir.is_dir():
                    for template_file in provider_dir.glob("*.yaml"):
                        self.load_template_from_file(template_file)
                    for template_file in provider_dir.glob("*.yml"):
                        self.load_template_from_file(template_file)

    @beartype
    @require(lambda self, provider: provider is None or isinstance(provider, str), "Provider must be str or None")
    @require(lambda self, framework: framework is None or isinstance(framework, str), "Framework must be str or None")
    @require(lambda self, persona: persona is None or isinstance(persona, str), "Persona must be str or None")
    @ensure(lambda result: result is None or isinstance(result, BacklogTemplate), "Must return BacklogTemplate or None")
    def resolve_template(
        self,
        provider: str | None = None,
        framework: str | None = None,
        persona: str | None = None,
        template_id: str | None = None,
    ) -> BacklogTemplate | None:
        """
        Resolve template using priority-based fallback chain.

        Priority order (most specific to least specific):
        1. provider+framework+persona
        2. provider+framework
        3. framework+persona
        4. framework
        5. provider+persona
        6. persona
        7. provider
        8. default (first corporate template)

        Args:
            provider: Provider name (github, ado, jira, linear)
            framework: Framework name (agile, scrum, safe, kanban)
            persona: Persona name (product-owner, architect, developer)
            template_id: Explicit template ID (overrides all filters)

        Returns:
            BacklogTemplate if found, None otherwise
        """
        # If explicit template_id provided, return it directly
        if template_id:
            return self.get_template(template_id)

        # Priority-based resolution with fallback chain
        candidates: list[BacklogTemplate] = []
        all_templates = self.list_templates(scope="corporate")

        # Try each priority level
        priority_checks = [
            # 1. provider+framework+persona (most specific)
            (
                lambda t: (provider and t.provider == provider)
                and (framework and t.framework == framework)
                and (persona and persona in t.personas),
                "provider+framework+persona",
            ),
            # 2. provider+framework
            (
                lambda t: (provider and t.provider == provider) and (framework and t.framework == framework),
                "provider+framework",
            ),
            # 3. framework+persona
            (
                lambda t: (framework and t.framework == framework) and (persona and persona in t.personas),
                "framework+persona",
            ),
            # 4. framework
            (lambda t: framework and t.framework == framework, "framework"),
            # 5. provider+persona
            (
                lambda t: (provider and t.provider == provider) and (persona and persona in t.personas),
                "provider+persona",
            ),
            # 6. persona
            (lambda t: persona and persona in t.personas, "persona"),
            # 7. provider
            (lambda t: provider and t.provider == provider, "provider"),
            # 8. default (framework-agnostic, persona-agnostic, provider-agnostic)
            (
                lambda t: not t.framework and not t.personas and not t.provider,
                "default",
            ),
        ]

        for check_func, _priority_name in priority_checks:
            candidates = [t for t in all_templates if check_func(t)]
            if candidates:
                # Return first match (can be enhanced to pick best match if multiple)
                return candidates[0]

        # No match found
        return None
