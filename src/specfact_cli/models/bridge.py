"""
Bridge configuration models for tool integration.

This module provides models for configurable bridge patterns that map SpecFact
logical concepts to physical tool artifacts (e.g., Spec-Kit, Linear, Jira).
This enables zero-code compatibility when tool structures change and supports
future tool integrations using the same interface pattern.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from beartype import beartype
from icontract import ensure, require
from pydantic import BaseModel, Field

from specfact_cli.utils.structured_io import StructuredFormat, dump_structured_file, load_structured_file


class AdapterType(str, Enum):
    """Supported adapter types."""

    SPECKIT = "speckit"
    GENERIC_MARKDOWN = "generic-markdown"
    GITHUB = "github"  # DevOps backlog tracking
    OPENSPEC = "openspec"  # OpenSpec integration
    ADO = "ado"  # Azure DevOps (future)
    LINEAR = "linear"  # Future
    JIRA = "jira"  # Future
    NOTION = "notion"  # Future


class ArtifactMapping(BaseModel):
    """Maps SpecFact logical concepts to physical tool paths."""

    path_pattern: str = Field(..., description="Dynamic path pattern (e.g., 'specs/{feature_id}/spec.md')")
    format: str = Field(default="markdown", description="File format: markdown, yaml, json")
    sync_target: str | None = Field(default=None, description="Optional external sync target (e.g., 'github_issues')")

    @beartype
    @require(lambda self: len(self.path_pattern) > 0, "Path pattern must not be empty")
    @ensure(lambda result: isinstance(result, Path), "Must return Path")
    def resolve_path(self, context: dict[str, str], base_path: Path | None = None) -> Path:
        """
        Resolve dynamic path pattern with context variables.

        Args:
            context: Context variables for path pattern (e.g., {'feature_id': '001-auth'})
            base_path: Base path to resolve relative paths (default: current directory)

        Returns:
            Resolved Path object
        """
        if base_path is None:
            base_path = Path.cwd()

        try:
            resolved = self.path_pattern.format(**context)
            return (base_path / resolved).resolve()
        except KeyError as e:
            msg = f"Missing context variable for path pattern: {e}"
            raise ValueError(msg) from e


class CommandMapping(BaseModel):
    """Maps tool commands to SpecFact triggers."""

    trigger: str = Field(..., description="Tool command (e.g., '/speckit.specify')")
    input_ref: str = Field(..., description="Input artifact reference (e.g., 'specification')")
    output_ref: str | None = Field(default=None, description="Output artifact reference (e.g., 'plan')")


class TemplateMapping(BaseModel):
    """Maps SpecFact schemas to tool prompt templates."""

    root_dir: str = Field(..., description="Template root directory (e.g., '.specify/prompts')")
    mapping: dict[str, str] = Field(..., description="Schema -> template file mapping")

    @beartype
    @require(lambda self: len(self.root_dir) > 0, "Root directory must not be empty")
    @ensure(lambda result: isinstance(result, Path), "Must return Path")
    def resolve_template_path(self, schema_key: str, base_path: Path | None = None) -> Path:
        """
        Resolve template path for a schema key.

        Args:
            schema_key: Schema key (e.g., 'specification', 'plan')
            base_path: Base path to resolve relative paths (default: current directory)

        Returns:
            Resolved template Path object
        """
        if base_path is None:
            base_path = Path.cwd()

        if schema_key not in self.mapping:
            msg = f"Schema key '{schema_key}' not found in template mapping"
            raise ValueError(msg)

        template_file = self.mapping[schema_key]
        return (base_path / self.root_dir / template_file).resolve()


class BridgeConfig(BaseModel):
    """
    Bridge configuration (translation layer between SpecFact and external tools).

    This configuration maps logical SpecFact concepts to physical tool artifacts,
    enabling zero-code compatibility when tool structures change.
    """

    version: str = Field(default="1.0", description="Bridge config schema version")
    adapter: AdapterType = Field(..., description="Adapter type (speckit, generic-markdown, openspec, etc.)")

    # Artifact mappings: Logical SpecFact concepts -> Physical tool paths
    artifacts: dict[str, ArtifactMapping] = Field(..., description="Artifact path mappings")

    # Cross-repository support: Base path for external tool repository
    external_base_path: Path | None = Field(
        default=None,
        description="Base path for external tool repository (for cross-repo integrations). "
        "When set, all artifact paths are resolved relative to this path instead of repo_path.",
    )

    # Command mappings: Tool commands -> SpecFact triggers
    commands: dict[str, CommandMapping] = Field(default_factory=dict, description="Command mappings")

    # Template mappings: SpecFact schemas -> Tool templates
    templates: TemplateMapping | None = Field(default=None, description="Template mappings")

    @beartype
    @classmethod
    @require(lambda path: path.exists(), "Bridge config file must exist")
    @ensure(lambda result: isinstance(result, BridgeConfig), "Must return BridgeConfig")
    def load_from_file(cls, path: Path) -> BridgeConfig:
        """
        Load bridge configuration from YAML file.

        Args:
            path: Path to bridge configuration YAML file

        Returns:
            Loaded BridgeConfig instance
        """
        data = load_structured_file(path)
        return cls(**data)

    @beartype
    @require(lambda path: path.parent.exists(), "Bridge config directory must exist")
    def save_to_file(self, path: Path) -> None:
        """
        Save bridge configuration to YAML file.

        Args:
            path: Path to save bridge configuration YAML file
        """
        dump_structured_file(self.model_dump(mode="json"), path, StructuredFormat.YAML)

    @beartype
    @require(lambda self, artifact_key: artifact_key in self.artifacts, "Artifact key must exist in artifacts")
    @ensure(lambda result: isinstance(result, Path), "Must return Path")
    def resolve_path(self, artifact_key: str, context: dict[str, str], base_path: Path | None = None) -> Path:
        """
        Resolve dynamic path pattern with context variables.

        Args:
            artifact_key: Artifact key (e.g., 'specification', 'plan')
            context: Context variables for path pattern (e.g., {'feature_id': '001-auth'})
            base_path: Base path to resolve relative paths (default: current directory)

        Returns:
            Resolved Path object
        """
        artifact = self.artifacts[artifact_key]
        # Use external_base_path if set, otherwise use provided base_path
        if self.external_base_path is not None:
            base_path = self.external_base_path
        return artifact.resolve_path(context, base_path)

    @beartype
    @require(lambda self, command_key: command_key in self.commands, "Command key must exist in commands")
    @ensure(lambda result: isinstance(result, CommandMapping), "Must return CommandMapping")
    def get_command(self, command_key: str) -> CommandMapping:
        """
        Get command mapping by key.

        Args:
            command_key: Command key (e.g., 'analyze', 'plan')

        Returns:
            CommandMapping instance
        """
        return self.commands[command_key]

    @beartype
    @require(lambda self: self.templates is not None, "Templates must be configured")
    @ensure(lambda result: isinstance(result, Path), "Must return Path")
    def resolve_template_path(self, schema_key: str, base_path: Path | None = None) -> Path:
        """
        Resolve template path for a schema key.

        Args:
            schema_key: Schema key (e.g., 'specification', 'plan')
            base_path: Base path to resolve relative paths (default: current directory)

        Returns:
            Resolved template Path object
        """
        if self.templates is None:
            msg = "Templates not configured in bridge config"
            raise ValueError(msg)

        return self.templates.resolve_template_path(schema_key, base_path)

    @beartype
    @classmethod
    @ensure(lambda result: isinstance(result, BridgeConfig), "Must return BridgeConfig")
    def preset_speckit_classic(cls) -> BridgeConfig:
        """
        Create Spec-Kit classic layout bridge preset.

        Returns:
            BridgeConfig for Spec-Kit classic layout (specs/ at root)
        """
        artifacts = {
            "specification": ArtifactMapping(
                path_pattern="specs/{feature_id}/spec.md",
                format="markdown",
            ),
            "plan": ArtifactMapping(
                path_pattern="specs/{feature_id}/plan.md",
                format="markdown",
            ),
            "tasks": ArtifactMapping(
                path_pattern="specs/{feature_id}/tasks.md",
                format="markdown",
                sync_target="github_issues",
            ),
            "contracts": ArtifactMapping(
                path_pattern="specs/{feature_id}/contracts/{contract_name}.yaml",
                format="yaml",
            ),
            "constitution": ArtifactMapping(
                path_pattern=".specify/memory/constitution.md",
                format="markdown",
            ),
        }

        commands = {
            "analyze": CommandMapping(
                trigger="/speckit.specify",
                input_ref="specification",
            ),
            "plan": CommandMapping(
                trigger="/speckit.plan",
                input_ref="specification",
                output_ref="plan",
            ),
        }

        templates = TemplateMapping(
            root_dir=".specify/prompts",
            mapping={
                "specification": "specify.md",
                "plan": "plan.md",
                "tasks": "tasks.md",
            },
        )

        return cls(
            adapter=AdapterType.SPECKIT,
            artifacts=artifacts,
            commands=commands,
            templates=templates,
        )

    @beartype
    @classmethod
    @ensure(lambda result: isinstance(result, BridgeConfig), "Must return BridgeConfig")
    def preset_speckit_specify(cls) -> BridgeConfig:
        """
        Create Spec-Kit specify layout bridge preset (canonical format).

        This is the canonical Spec-Kit layout where specs are inside .specify/specs/.
        According to Spec-Kit documentation, this is the recommended structure.

        Returns:
            BridgeConfig for Spec-Kit specify layout (.specify/specs/)
        """
        artifacts = {
            "specification": ArtifactMapping(
                path_pattern=".specify/specs/{feature_id}/spec.md",
                format="markdown",
            ),
            "plan": ArtifactMapping(
                path_pattern=".specify/specs/{feature_id}/plan.md",
                format="markdown",
            ),
            "tasks": ArtifactMapping(
                path_pattern=".specify/specs/{feature_id}/tasks.md",
                format="markdown",
                sync_target="github_issues",
            ),
            "contracts": ArtifactMapping(
                path_pattern=".specify/specs/{feature_id}/contracts/{contract_name}.yaml",
                format="yaml",
            ),
            "constitution": ArtifactMapping(
                path_pattern=".specify/memory/constitution.md",
                format="markdown",
            ),
        }

        commands = {
            "analyze": CommandMapping(
                trigger="/speckit.specify",
                input_ref="specification",
            ),
            "plan": CommandMapping(
                trigger="/speckit.plan",
                input_ref="specification",
                output_ref="plan",
            ),
        }

        templates = TemplateMapping(
            root_dir=".specify/prompts",
            mapping={
                "specification": "specify.md",
                "plan": "plan.md",
                "tasks": "tasks.md",
            },
        )

        return cls(
            adapter=AdapterType.SPECKIT,
            artifacts=artifacts,
            commands=commands,
            templates=templates,
        )

    @beartype
    @classmethod
    @ensure(lambda result: isinstance(result, BridgeConfig), "Must return BridgeConfig")
    def preset_speckit_modern(cls) -> BridgeConfig:
        """
        Create Spec-Kit modern layout bridge preset.

        Returns:
            BridgeConfig for Spec-Kit modern layout (docs/specs/)
        """
        artifacts = {
            "specification": ArtifactMapping(
                path_pattern="docs/specs/{feature_id}/spec.md",
                format="markdown",
            ),
            "plan": ArtifactMapping(
                path_pattern="docs/specs/{feature_id}/plan.md",
                format="markdown",
            ),
            "tasks": ArtifactMapping(
                path_pattern="docs/specs/{feature_id}/tasks.md",
                format="markdown",
                sync_target="github_issues",
            ),
            "contracts": ArtifactMapping(
                path_pattern="docs/specs/{feature_id}/contracts/{contract_name}.yaml",
                format="yaml",
            ),
            "constitution": ArtifactMapping(
                path_pattern=".specify/memory/constitution.md",
                format="markdown",
            ),
        }

        commands = {
            "analyze": CommandMapping(
                trigger="/speckit.specify",
                input_ref="specification",
            ),
            "plan": CommandMapping(
                trigger="/speckit.plan",
                input_ref="specification",
                output_ref="plan",
            ),
        }

        templates = TemplateMapping(
            root_dir=".specify/prompts",
            mapping={
                "specification": "specify.md",
                "plan": "plan.md",
                "tasks": "tasks.md",
            },
        )

        return cls(
            adapter=AdapterType.SPECKIT,
            artifacts=artifacts,
            commands=commands,
            templates=templates,
        )

    @beartype
    @classmethod
    @ensure(lambda result: isinstance(result, BridgeConfig), "Must return BridgeConfig")
    def preset_generic_markdown(cls) -> BridgeConfig:
        """
        Create generic markdown bridge preset.

        Returns:
            BridgeConfig for generic markdown (minimal configuration)
        """
        artifacts = {
            "specification": ArtifactMapping(
                path_pattern="specs/{feature_id}/spec.md",
                format="markdown",
            ),
        }

        return cls(
            adapter=AdapterType.GENERIC_MARKDOWN,
            artifacts=artifacts,
        )

    @beartype
    @classmethod
    @ensure(lambda result: isinstance(result, BridgeConfig), "Must return BridgeConfig")
    def preset_github(cls) -> BridgeConfig:
        """
        Create GitHub bridge preset for DevOps backlog tracking.

        GitHub-specific configuration (repo_owner, repo_name, api_token) should be
        provided via environment variables (GITHUB_TOKEN) or CLI options, not stored
        in bridge config for security reasons.

        Returns:
            BridgeConfig for GitHub adapter (export-only mode for change proposals)
        """
        artifacts = {
            "change_proposal": ArtifactMapping(
                path_pattern="api/repos/{repo_owner}/{repo_name}/issues",
                format="api",
                sync_target="github_issues",
            ),
            "change_status": ArtifactMapping(
                path_pattern="api/repos/{repo_owner}/{repo_name}/issues/{issue_number}",
                format="api",
                sync_target="github_issues",
            ),
        }

        return cls(
            adapter=AdapterType.GITHUB,
            artifacts=artifacts,
        )

    @beartype
    @classmethod
    @ensure(lambda result: isinstance(result, BridgeConfig), "Must return BridgeConfig")
    def preset_ado(cls) -> BridgeConfig:
        """
        Create Azure DevOps bridge preset for DevOps backlog tracking.

        Azure DevOps-specific configuration (org, project, base_url, api_token, work_item_type)
        should be provided via environment variables (AZURE_DEVOPS_TOKEN) or CLI options,
        not stored in bridge config for security reasons.

        Returns:
            BridgeConfig for Azure DevOps adapter (export-only mode for change proposals)
        """
        artifacts = {
            "change_proposal": ArtifactMapping(
                path_pattern="api/{org}/{project}/workitems",
                format="api",
                sync_target="ado_work_items",
            ),
            "change_status": ArtifactMapping(
                path_pattern="api/{org}/{project}/workitems/{work_item_id}",
                format="api",
                sync_target="ado_work_items",
            ),
        }

        return cls(
            adapter=AdapterType.ADO,
            artifacts=artifacts,
        )

    @beartype
    @classmethod
    @ensure(lambda result: isinstance(result, BridgeConfig), "Must return BridgeConfig")
    def preset_openspec(cls) -> BridgeConfig:
        """
        Create OpenSpec bridge preset.

        Returns:
            BridgeConfig for OpenSpec integration with artifact mappings for:
            - specification: openspec/specs/{feature_id}/spec.md
            - project_context: openspec/config.yaml (OPSX) if present, else openspec/project.md (legacy)
            - change_proposal: openspec/changes/{change_name}/proposal.md
            - change_tasks: openspec/changes/{change_name}/tasks.md
            - change_spec_delta: openspec/changes/{change_name}/specs/{feature_id}/spec.md
        """
        artifacts = {
            "specification": ArtifactMapping(
                path_pattern="openspec/specs/{feature_id}/spec.md",
                format="markdown",
            ),
            "project_context": ArtifactMapping(
                path_pattern="openspec/project.md",
                format="markdown",
            ),
            "change_proposal": ArtifactMapping(
                path_pattern="openspec/changes/{change_name}/proposal.md",
                format="markdown",
            ),
            "change_tasks": ArtifactMapping(
                path_pattern="openspec/changes/{change_name}/tasks.md",
                format="markdown",
            ),
            "change_spec_delta": ArtifactMapping(
                path_pattern="openspec/changes/{change_name}/specs/{feature_id}/spec.md",
                format="markdown",
            ),
        }

        return cls(
            adapter=AdapterType.OPENSPEC,
            artifacts=artifacts,
        )
