"""
Template registry for backlog item templates.

This module provides centralized template management with detection, matching,
and scoping capabilities (corporate, team, user).
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

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


def _tpl_match_pfp(t: BacklogTemplate, provider: str | None, framework: str | None, persona: str | None) -> bool:
    return bool(
        provider
        and t.provider == provider
        and framework
        and t.framework == framework
        and persona
        and persona in t.personas
    )


def _tpl_match_pf(t: BacklogTemplate, provider: str | None, framework: str | None, _persona: str | None) -> bool:
    return bool(provider and t.provider == provider and framework and t.framework == framework)


def _tpl_match_fp(t: BacklogTemplate, _provider: str | None, framework: str | None, persona: str | None) -> bool:
    return bool(framework and t.framework == framework and persona and persona in t.personas)


def _tpl_match_f(t: BacklogTemplate, _provider: str | None, framework: str | None, _persona: str | None) -> bool:
    return bool(framework and t.framework == framework)


def _tpl_match_pp(t: BacklogTemplate, provider: str | None, _framework: str | None, persona: str | None) -> bool:
    return bool(provider and t.provider == provider and persona and persona in t.personas)


def _tpl_match_persona(t: BacklogTemplate, _provider: str | None, _framework: str | None, persona: str | None) -> bool:
    return bool(persona and persona in t.personas)


def _tpl_match_provider(t: BacklogTemplate, provider: str | None, _framework: str | None, _persona: str | None) -> bool:
    return bool(provider and t.provider == provider)


def _tpl_match_default(t: BacklogTemplate, _provider: str | None, _framework: str | None, _persona: str | None) -> bool:
    return not t.framework and not t.personas and not t.provider


_TEMPLATE_PRIORITY_PREDICATES: tuple[
    tuple[str, Callable[[BacklogTemplate, str | None, str | None, str | None], bool]], ...
] = (
    ("provider+framework+persona", _tpl_match_pfp),
    ("provider+framework", _tpl_match_pf),
    ("framework+persona", _tpl_match_fp),
    ("framework", _tpl_match_f),
    ("provider+persona", _tpl_match_pp),
    ("persona", _tpl_match_persona),
    ("provider", _tpl_match_provider),
    ("default", _tpl_match_default),
)


def _str_list_from_yaml(raw_val: Any) -> list[str]:
    return [str(x) for x in raw_val] if isinstance(raw_val, list) else []


def _backlog_template_from_yaml_raw(raw: dict[str, Any], template_path: Path) -> BacklogTemplate:
    body_pat = raw.get("body_patterns", {})
    body_patterns: dict[str, str] = {str(k): str(v) for k, v in body_pat.items()} if isinstance(body_pat, dict) else {}
    return BacklogTemplate(
        template_id=str(raw.get("template_id", template_path.stem)),
        name=str(raw.get("name", "")),
        description=str(raw.get("description", "")),
        scope=str(raw.get("scope", "corporate")),
        team_id=cast(str | None, raw.get("team_id")),
        personas=_str_list_from_yaml(raw.get("personas", [])),
        framework=cast(str | None, raw.get("framework")),
        provider=cast(str | None, raw.get("provider")),
        required_sections=_str_list_from_yaml(raw.get("required_sections", [])),
        optional_sections=_str_list_from_yaml(raw.get("optional_sections", [])),
        body_patterns=body_patterns,
        title_patterns=_str_list_from_yaml(raw.get("title_patterns", [])),
        schema_ref=cast(str | None, raw.get("schema_ref")),
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

                raw = cast(dict[str, Any], data)
                self.register_template(_backlog_template_from_yaml_raw(raw, template_path))
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

        defaults_dir = template_dir / "defaults"
        root_to_scan = defaults_dir if defaults_dir.exists() else template_dir
        self._load_yaml_templates_in_dir(root_to_scan)

        for sub in ("frameworks", "personas", "providers"):
            self._load_yaml_templates_from_subdirs(template_dir / sub)

    def _load_yaml_templates_in_dir(self, directory: Path) -> None:
        for pattern in ("*.yaml", "*.yml"):
            for template_file in directory.glob(pattern):
                self.load_template_from_file(template_file)

    def _load_yaml_templates_from_subdirs(self, base_dir: Path) -> None:
        if not base_dir.is_dir():
            return
        for child in base_dir.iterdir():
            if child.is_dir():
                self._load_yaml_templates_in_dir(child)

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
        if template_id:
            return self.get_template(template_id)

        all_templates = self.list_templates(scope="corporate")
        for _name, check_func in _TEMPLATE_PRIORITY_PREDICATES:
            for t in all_templates:
                if check_func(t, provider, framework, persona):
                    return t
        return None
