"""
Bridge probe for detecting tool configurations and auto-generating bridge configs.

This module provides functionality to detect tool versions, directory layouts,
and generate appropriate bridge configurations for Spec-Kit and future tool integrations.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from beartype import beartype
from icontract import ensure, require

from specfact_cli.models.bridge import AdapterType, ArtifactMapping, BridgeConfig, CommandMapping, TemplateMapping
from specfact_cli.utils.structure import SpecFactStructure


@dataclass
class ToolCapabilities:
    """Detected tool capabilities and configuration."""

    tool: str  # Tool name (e.g., "speckit")
    version: str | None = None  # Tool version if detectable
    layout: str = "classic"  # Layout type: "classic" or "modern"
    specs_dir: str = "specs"  # Specs directory path (relative to repo root)
    has_external_config: bool = False  # Has external configuration files
    has_custom_hooks: bool = False  # Has custom hooks or scripts


class BridgeProbe:
    """
    Probe for detecting tool configurations and generating bridge configs.

    At runtime, detects tool version, directory layout, and presence of external
    config/hooks to auto-generate or validate bridge configuration.
    """

    @beartype
    @require(lambda repo_path: repo_path.exists(), "Repository path must exist")
    @require(lambda repo_path: repo_path.is_dir(), "Repository path must be a directory")
    def __init__(self, repo_path: Path) -> None:
        """
        Initialize bridge probe.

        Args:
            repo_path: Path to repository root
        """
        self.repo_path = Path(repo_path).resolve()

    @beartype
    @ensure(lambda result: isinstance(result, ToolCapabilities), "Must return ToolCapabilities")
    def detect(self) -> ToolCapabilities:
        """
        Detect tool capabilities and configuration.

        Returns:
            ToolCapabilities instance with detected information
        """
        # Try to detect Spec-Kit first (most common)
        if self._is_speckit_repo():
            return self._detect_speckit()
        # Future: Add detection for other tools (Linear, Jira, etc.)

        # Default: Unknown tool
        return ToolCapabilities(tool="unknown")

    @beartype
    @ensure(lambda result: isinstance(result, bool), "Must return boolean")
    def _is_speckit_repo(self) -> bool:
        """
        Check if repository is a Spec-Kit project.

        Returns:
            True if Spec-Kit structure detected, False otherwise
        """
        specify_dir = self.repo_path / ".specify"
        return specify_dir.exists() and specify_dir.is_dir()

    @beartype
    @ensure(lambda result: isinstance(result, ToolCapabilities), "Must return ToolCapabilities")
    def _detect_speckit(self) -> ToolCapabilities:
        """
        Detect Spec-Kit capabilities and configuration.

        Returns:
            ToolCapabilities instance for Spec-Kit
        """
        capabilities = ToolCapabilities(tool="speckit")

        # Detect layout (classic vs modern)
        # Classic: specs/ directory at root
        # Modern: docs/specs/ directory
        specs_classic = self.repo_path / "specs"
        specs_modern = self.repo_path / "docs" / "specs"

        if specs_modern.exists():
            capabilities.layout = "modern"
            capabilities.specs_dir = "docs/specs"
        elif specs_classic.exists():
            capabilities.layout = "classic"
            capabilities.specs_dir = "specs"
        else:
            # Default to classic if neither exists (will be created)
            capabilities.layout = "classic"
            capabilities.specs_dir = "specs"

        # Try to detect version from .specify directory structure
        specify_dir = self.repo_path / ".specify"
        if specify_dir.exists():
            # Check for version indicators (e.g., prompts version, memory structure)
            prompts_dir = specify_dir / "prompts"
            memory_dir = specify_dir / "memory"
            if prompts_dir.exists() and memory_dir.exists():
                # Modern Spec-Kit structure
                capabilities.version = "0.0.85+"  # Approximate version detection
            elif memory_dir.exists():
                # Classic structure
                capabilities.version = "0.0.80+"  # Approximate version detection

        # Check for external configuration
        config_files = [
            ".specify/config.yaml",
            ".specify/config.yml",
            "speckit.config.yaml",
            "speckit.config.yml",
        ]
        for config_file in config_files:
            if (self.repo_path / config_file).exists():
                capabilities.has_external_config = True
                break

        # Check for custom hooks
        hooks_dir = specify_dir / "hooks"
        if hooks_dir.exists() and any(hooks_dir.iterdir()):
            capabilities.has_custom_hooks = True

        return capabilities

    @beartype
    @require(lambda capabilities: capabilities.tool in ["speckit", "unknown"], "Tool must be supported")
    @ensure(lambda result: isinstance(result, BridgeConfig), "Must return BridgeConfig")
    def auto_generate_bridge(self, capabilities: ToolCapabilities) -> BridgeConfig:
        """
        Auto-generate bridge configuration based on detected capabilities.

        Args:
            capabilities: Detected tool capabilities

        Returns:
            Generated BridgeConfig instance
        """
        if capabilities.tool == "speckit":
            return self._generate_speckit_bridge(capabilities)

        # Default: Generic markdown bridge
        return self._generate_generic_markdown_bridge()

    @beartype
    @ensure(lambda result: isinstance(result, BridgeConfig), "Must return BridgeConfig")
    def _generate_speckit_bridge(self, capabilities: ToolCapabilities) -> BridgeConfig:
        """
        Generate Spec-Kit bridge configuration.

        Args:
            capabilities: Spec-Kit capabilities

        Returns:
            BridgeConfig for Spec-Kit
        """
        # Determine feature ID pattern based on detected structure
        # Classic: specs/001-feature-name/
        # Modern: docs/specs/001-feature-name/
        feature_id_pattern = "{feature_id}"  # Will be resolved at runtime

        # Artifact mappings
        artifacts = {
            "specification": ArtifactMapping(
                path_pattern=f"{capabilities.specs_dir}/{feature_id_pattern}/spec.md",
                format="markdown",
            ),
            "plan": ArtifactMapping(
                path_pattern=f"{capabilities.specs_dir}/{feature_id_pattern}/plan.md",
                format="markdown",
            ),
            "tasks": ArtifactMapping(
                path_pattern=f"{capabilities.specs_dir}/{feature_id_pattern}/tasks.md",
                format="markdown",
                sync_target="github_issues",  # Optional: link to external sync
            ),
            "contracts": ArtifactMapping(
                path_pattern=f"{capabilities.specs_dir}/{feature_id_pattern}/contracts/{{contract_name}}.yaml",
                format="yaml",
            ),
        }

        # Command mappings
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

        # Template mappings (if .specify/prompts exists)
        templates = None
        specify_dir = self.repo_path / ".specify"
        prompts_dir = specify_dir / "prompts"
        if prompts_dir.exists():
            template_mapping: dict[str, str] = {}
            # Check for common template files
            if (prompts_dir / "specify.md").exists():
                template_mapping["specification"] = "specify.md"
            if (prompts_dir / "plan.md").exists():
                template_mapping["plan"] = "plan.md"
            if (prompts_dir / "tasks.md").exists():
                template_mapping["tasks"] = "tasks.md"

            if template_mapping:
                templates = TemplateMapping(
                    root_dir=".specify/prompts",
                    mapping=template_mapping,
                )

        return BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts=artifacts,
            commands=commands,
            templates=templates,
        )

    @beartype
    @ensure(lambda result: isinstance(result, BridgeConfig), "Must return BridgeConfig")
    def _generate_generic_markdown_bridge(self) -> BridgeConfig:
        """
        Generate generic markdown bridge configuration.

        Returns:
            BridgeConfig for generic markdown
        """
        artifacts = {
            "specification": ArtifactMapping(
                path_pattern="specs/{feature_id}/spec.md",
                format="markdown",
            ),
        }

        return BridgeConfig(
            adapter=AdapterType.GENERIC_MARKDOWN,
            artifacts=artifacts,
        )

    @beartype
    @require(lambda bridge_config: isinstance(bridge_config, BridgeConfig), "Bridge config must be BridgeConfig")
    @ensure(lambda result: isinstance(result, dict), "Must return dictionary")
    def validate_bridge(self, bridge_config: BridgeConfig) -> dict[str, list[str]]:
        """
        Validate bridge configuration and check if paths exist.

        Args:
            bridge_config: Bridge configuration to validate

        Returns:
            Dictionary with validation results:
            - "errors": List of error messages
            - "warnings": List of warning messages
            - "suggestions": List of suggestions
        """
        errors: list[str] = []
        warnings: list[str] = []
        suggestions: list[str] = []

        # Check if artifact paths exist (sample check with common feature IDs)
        sample_feature_ids = ["001-auth", "002-payment", "test-feature"]
        for artifact_key, artifact in bridge_config.artifacts.items():
            found_paths = 0
            for feature_id in sample_feature_ids:
                try:
                    context = {"feature_id": feature_id}
                    if "contract_name" in artifact.path_pattern:
                        context["contract_name"] = "api"
                    resolved_path = bridge_config.resolve_path(artifact_key, context, base_path=self.repo_path)
                    if resolved_path.exists():
                        found_paths += 1
                except (ValueError, KeyError):
                    # Missing context variable or invalid pattern
                    pass

            if found_paths == 0:
                # No paths found - might be new project or wrong pattern
                warnings.append(
                    f"Artifact '{artifact_key}' pattern '{artifact.path_pattern}' - no matching files found. "
                    "This might be normal for new projects."
                )

        # Check template paths if configured
        if bridge_config.templates:
            for schema_key in bridge_config.templates.mapping:
                try:
                    template_path = bridge_config.resolve_template_path(schema_key, base_path=self.repo_path)
                    if not template_path.exists():
                        warnings.append(
                            f"Template for '{schema_key}' not found at {template_path}. "
                            "Bridge will work but templates won't be available."
                        )
                except ValueError as e:
                    errors.append(f"Template resolution error for '{schema_key}': {e}")

        # Suggest corrections based on common issues
        if bridge_config.adapter == AdapterType.SPECKIT:
            # Check if specs/ exists but bridge points to docs/specs/
            specs_classic = self.repo_path / "specs"
            if specs_classic.exists():
                for artifact in bridge_config.artifacts.values():
                    if "docs/specs" in artifact.path_pattern:
                        suggestions.append(
                            "Found 'specs/' directory but bridge points to 'docs/specs/'. "
                            "Consider updating bridge config to use 'specs/' pattern."
                        )
                        break

            # Check if docs/specs/ exists but bridge points to specs/
            specs_modern = self.repo_path / "docs" / "specs"
            if specs_modern.exists():
                for artifact in bridge_config.artifacts.values():
                    if artifact.path_pattern.startswith("specs/") and "docs" not in artifact.path_pattern:
                        suggestions.append(
                            "Found 'docs/specs/' directory but bridge points to 'specs/'. "
                            "Consider updating bridge config to use 'docs/specs/' pattern."
                        )
                        break

        return {
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions,
        }

    @beartype
    @require(lambda bridge_config: isinstance(bridge_config, BridgeConfig), "Bridge config must be BridgeConfig")
    @ensure(lambda result: result is None, "Must return None")
    def save_bridge_config(self, bridge_config: BridgeConfig, overwrite: bool = False) -> None:
        """
        Save bridge configuration to `.specfact/config/bridge.yaml`.

        Args:
            bridge_config: Bridge configuration to save
            overwrite: If True, overwrite existing config; if False, raise error if exists
        """
        config_dir = self.repo_path / SpecFactStructure.CONFIG
        config_dir.mkdir(parents=True, exist_ok=True)

        bridge_path = config_dir / "bridge.yaml"
        if bridge_path.exists() and not overwrite:
            msg = f"Bridge config already exists at {bridge_path}. Use overwrite=True to replace."
            raise FileExistsError(msg)

        bridge_config.save_to_file(bridge_path)
