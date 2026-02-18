"""Policy engine configuration model and loader."""

from __future__ import annotations

from pathlib import Path

import yaml
from beartype import beartype
from icontract import ensure
from pydantic import BaseModel, Field


POLICY_DOCS_HINT = "See docs/guides/agile-scrum-workflows.md#policy-engine-commands-dordodflowpi for format details."


@beartype
class ScrumPolicyConfig(BaseModel):
    """Scrum policy configuration."""

    dor_required_fields: list[str] = Field(default_factory=list, description="DoR required fields.")
    dod_required_fields: list[str] = Field(default_factory=list, description="DoD required fields.")


@beartype
class KanbanColumnPolicyConfig(BaseModel):
    """Kanban column policy configuration."""

    entry_required_fields: list[str] = Field(default_factory=list, description="Fields required to enter column.")
    exit_required_fields: list[str] = Field(default_factory=list, description="Fields required to exit column.")


@beartype
class KanbanPolicyConfig(BaseModel):
    """Kanban policy configuration."""

    columns: dict[str, KanbanColumnPolicyConfig] = Field(default_factory=dict, description="Column rule map.")


@beartype
class SafePolicyConfig(BaseModel):
    """SAFe policy configuration."""

    pi_readiness_required_fields: list[str] = Field(default_factory=list, description="PI readiness required fields.")


@beartype
class PolicyConfig(BaseModel):
    """Root policy configuration."""

    scrum: ScrumPolicyConfig = Field(default_factory=ScrumPolicyConfig)
    kanban: KanbanPolicyConfig = Field(default_factory=KanbanPolicyConfig)
    safe: SafePolicyConfig = Field(default_factory=SafePolicyConfig)


@beartype
@ensure(lambda result: isinstance(result, tuple), "Loader must return tuple")
def load_policy_config(repo_path: Path) -> tuple[PolicyConfig | None, str | None]:
    """Load .specfact/policy.yaml from repository root without raising to callers."""
    config_path = repo_path / ".specfact" / "policy.yaml"
    if not config_path.exists():
        return None, f"Policy config not found: {config_path}\n{POLICY_DOCS_HINT}"

    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        if raw is None:
            raw = {}
        if not isinstance(raw, dict):
            return None, f"Invalid policy config format: expected mapping in {config_path}\n{POLICY_DOCS_HINT}"
        return PolicyConfig.model_validate(raw), None
    except Exception as exc:
        return None, f"Invalid policy config in {config_path}: {exc}\n{POLICY_DOCS_HINT}"
