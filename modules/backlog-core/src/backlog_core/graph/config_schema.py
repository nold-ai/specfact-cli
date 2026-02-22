"""Backlog graph configuration schema and loading helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class DependencyConfig(BaseModel):
    """Dependency mapping configuration."""

    template: str | None = Field(default=None, description="Selected mapping template")
    type_mapping: dict[str, str] = Field(default_factory=dict, description="Raw type -> normalized type mapping")
    dependency_rules: dict[str, str] = Field(default_factory=dict, description="Raw relation -> normalized mapping")
    status_mapping: dict[str, str] = Field(default_factory=dict, description="Raw status -> normalized status mapping")
    creation_hierarchy: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Allowed parent types per child type",
    )


class ProviderConfig(BaseModel):
    """Provider-specific backlog connection configuration."""

    adapter: str | None = Field(default=None, description="Adapter identifier (github, ado, jira, ...) ")
    project_id: str | None = Field(default=None, description="Project ID/repo/board identifier")
    settings: dict[str, Any] = Field(default_factory=dict, description="Provider-specific extra settings")


class DevOpsStageConfig(BaseModel):
    """Stage-level workflow defaults for integrated DevOps commands."""

    default_action: str | None = Field(default=None, description="Default action name for the stage")
    enabled: bool = Field(default=True, description="Whether stage is enabled")
    settings: dict[str, Any] = Field(default_factory=dict, description="Optional stage-specific settings")


class BacklogConfigSchema(BaseModel):
    """Project-level backlog configuration schema."""

    dependencies: DependencyConfig = Field(default_factory=DependencyConfig)
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)
    devops_stages: dict[str, DevOpsStageConfig] = Field(default_factory=dict)


def _load_backlog_config_from_yaml(path: Path) -> BacklogConfigSchema | None:
    """Load and validate backlog config payload from a YAML file path."""
    if not path.exists():
        return None

    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        return None

    backlog_config = loaded.get("backlog_config")
    if not isinstance(backlog_config, dict):
        return None

    payload = dict(backlog_config)
    devops_stages = loaded.get("devops_stages")
    if isinstance(devops_stages, dict):
        payload["devops_stages"] = devops_stages

    return BacklogConfigSchema.model_validate(payload)


def load_backlog_config_from_spec(spec_path: Path) -> BacklogConfigSchema | None:
    """Load backlog config from `.specfact/spec.yaml` if present and valid."""
    return _load_backlog_config_from_yaml(spec_path)


def load_backlog_config_from_backlog_file(config_path: Path) -> BacklogConfigSchema | None:
    """Load backlog config from `.specfact/backlog-config.yaml` if present and valid."""
    return _load_backlog_config_from_yaml(config_path)
