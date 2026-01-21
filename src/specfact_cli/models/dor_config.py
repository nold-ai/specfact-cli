"""
Definition of Ready (DoR) configuration model.

This module provides DoR configuration for repo-level, team-level, and project-level
DoR rules that are checked before backlog items are ready for sprint planning.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require
from pydantic import BaseModel, Field


class DefinitionOfReady(BaseModel):
    """
    Definition of Ready (DoR) configuration.

    Defines rules that must be satisfied before a backlog item is ready
    to be added to a sprint or before work should start.
    """

    rules: dict[str, bool] = Field(
        default_factory=dict,
        description="DoR rules: {'story_points': True, 'value_points': True, 'priority': True, 'business_value': True, 'acceptance_criteria': True, 'dependencies': True}",
    )
    repo_path: Path | None = Field(default=None, description="Repository path this DoR config applies to")
    team_id: str | None = Field(default=None, description="Team ID this DoR config applies to (for team-level config)")
    project_id: str | None = Field(
        default=None, description="Project ID this DoR config applies to (for project-level config)"
    )

    @beartype
    @require(lambda self, item_data: isinstance(item_data, dict), "Item data must be dict")
    @ensure(lambda result: isinstance(result, list), "Must return list of error strings")
    def validate_item(self, item_data: dict[str, Any]) -> list[str]:
        """
        Validate backlog item against DoR rules.

        Args:
            item_data: Backlog item data (can be BacklogItem dict representation or raw provider data)

        Returns:
            List of validation errors (empty if all DoR rules satisfied)
        """
        errors: list[str] = []
        item_id = item_data.get("id") or item_data.get("number") or "UNKNOWN"
        context = f"Backlog item {item_id}"

        # Check story points (if rule enabled)
        if self.rules.get("story_points", False):
            story_points = item_data.get("story_points") or item_data.get("provider_fields", {}).get("story_points")
            if story_points is None:
                errors.append(f"{context}: Missing story points (required for DoR)")

        # Check value points (if rule enabled)
        if self.rules.get("value_points", False):
            value_points = item_data.get("value_points") or item_data.get("provider_fields", {}).get("value_points")
            if value_points is None:
                errors.append(f"{context}: Missing value points (required for DoR)")

        # Check priority (if rule enabled)
        if self.rules.get("priority", False):
            priority = item_data.get("priority") or item_data.get("provider_fields", {}).get("priority")
            if priority is None:
                errors.append(f"{context}: Missing priority (required for DoR)")

        # Check business value (if rule enabled)
        if self.rules.get("business_value", False):
            business_value = item_data.get("business_value") or item_data.get("body_markdown", "")
            # Check if body contains business value section
            if "business value" not in business_value.lower() and "value proposition" not in business_value.lower():
                errors.append(f"{context}: Missing business value description (required for DoR)")

        # Check acceptance criteria (if rule enabled)
        if self.rules.get("acceptance_criteria", False):
            body = item_data.get("body_markdown", "")
            # Check if body contains acceptance criteria section
            if "acceptance criteria" not in body.lower() and "acceptance" not in body.lower():
                errors.append(f"{context}: Missing acceptance criteria (required for DoR)")

        # Check dependencies are documented (if rule enabled)
        if self.rules.get("dependencies", False):
            # Dependencies might be in provider_fields or body
            dependencies = item_data.get("dependencies") or item_data.get("provider_fields", {}).get("dependencies", [])
            body = item_data.get("body_markdown", "")
            # Check if dependencies are mentioned in body or explicitly set
            if not dependencies and "depend" not in body.lower() and "block" not in body.lower():
                errors.append(f"{context}: Missing dependency documentation (required for DoR)")

        return errors

    @beartype
    @classmethod
    @require(lambda cls, config_path: isinstance(config_path, Path), "Config path must be Path")
    @ensure(lambda result: isinstance(result, DefinitionOfReady), "Must return DefinitionOfReady")
    def load_from_file(cls, config_path: Path) -> DefinitionOfReady:
        """
        Load DoR configuration from YAML file.

        Args:
            config_path: Path to DoR config YAML file (e.g., `.specfact/dor.yaml`)

        Returns:
            DefinitionOfReady instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file is malformed
        """
        if not config_path.exists():
            msg = f"DoR config file not found: {config_path}"
            raise FileNotFoundError(msg)

        import yaml

        try:
            with config_path.open() as f:
                data = yaml.safe_load(f)
                if not isinstance(data, dict):
                    msg = f"DoR config file must contain a YAML dict: {config_path}"
                    raise ValueError(msg)

                return cls(
                    rules=data.get("rules", {}),
                    repo_path=Path(data.get("repo_path", "")) if data.get("repo_path") else None,
                    team_id=data.get("team_id"),
                    project_id=data.get("project_id"),
                )
        except yaml.YAMLError as e:
            msg = f"Failed to parse DoR config YAML: {config_path}: {e}"
            raise ValueError(msg) from e

    @beartype
    @classmethod
    @require(lambda cls, repo_path: isinstance(repo_path, Path), "Repo path must be Path")
    @ensure(
        lambda result: result is None or isinstance(result, DefinitionOfReady), "Must return DefinitionOfReady or None"
    )
    def load_from_repo(cls, repo_path: Path) -> DefinitionOfReady | None:
        """
        Load DoR configuration from repository (checks `.specfact/dor.yaml`).

        Args:
            repo_path: Repository root path

        Returns:
            DefinitionOfReady instance if config found, None otherwise
        """
        config_path = repo_path / ".specfact" / "dor.yaml"
        if config_path.exists():
            try:
                return cls.load_from_file(config_path)
            except (FileNotFoundError, ValueError):
                return None
        return None
