"""
Bridge probe for detecting tool configurations and auto-generating bridge configs.

This module provides functionality to detect tool versions, directory layouts,
and generate appropriate bridge configurations using the adapter registry pattern.
"""

from __future__ import annotations

from pathlib import Path

from beartype import beartype
from icontract import ensure, require

from specfact_cli.adapters.registry import AdapterRegistry
from specfact_cli.models.bridge import BridgeConfig
from specfact_cli.models.capabilities import ToolCapabilities
from specfact_cli.utils.structure import SpecFactStructure


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
    def detect(self, bridge_config: BridgeConfig | None = None) -> ToolCapabilities:
        """
        Detect tool capabilities and configuration using adapter registry.

        This method loops through all registered adapters and calls their detect()
        methods. The first adapter that returns True is used to get capabilities.

        **Detection Priority**: Layout-specific adapters (SpecKit, OpenSpec) are tried
        before generic adapters (GitHub) to prevent false positives. A repository with
        a GitHub remote but SpecKit/OpenSpec layout should be detected as SpecKit/OpenSpec,
        not GitHub.

        Args:
            bridge_config: Optional bridge configuration (for cross-repo detection)

        Returns:
            ToolCapabilities instance with detected information
        """
        # Get all registered adapters
        all_adapters = AdapterRegistry.list_adapters()

        # Prioritize layout-specific adapters (check directory structure) over generic ones
        # Layout-specific adapters: speckit, openspec (check for specific directory layouts)
        # Generic adapters: github (only checks for GitHub remote, too generic)
        layout_specific_adapters = ["speckit", "openspec"]
        generic_adapters = ["github"]

        # Try layout-specific adapters first
        for adapter_type in layout_specific_adapters:
            if adapter_type in all_adapters:
                try:
                    adapter = AdapterRegistry.get_adapter(adapter_type)
                    if adapter.detect(self.repo_path, bridge_config):
                        # Layout-specific adapter detected this repository
                        return adapter.get_capabilities(self.repo_path, bridge_config)
                except Exception:
                    # Adapter failed to detect or get capabilities, try next one
                    continue

        # Then try generic adapters (fallback for repos without layout-specific structure)
        for adapter_type in generic_adapters:
            if adapter_type in all_adapters:
                try:
                    adapter = AdapterRegistry.get_adapter(adapter_type)
                    if adapter.detect(self.repo_path, bridge_config):
                        # Generic adapter detected this repository
                        return adapter.get_capabilities(self.repo_path, bridge_config)
                except Exception:
                    # Adapter failed to detect or get capabilities, try next one
                    continue

        # Finally try any remaining adapters not in the priority lists
        for adapter_type in all_adapters:
            if adapter_type not in layout_specific_adapters and adapter_type not in generic_adapters:
                try:
                    adapter = AdapterRegistry.get_adapter(adapter_type)
                    if adapter.detect(self.repo_path, bridge_config):
                        # Adapter detected this repository
                        return adapter.get_capabilities(self.repo_path, bridge_config)
                except Exception:
                    # Adapter failed to detect or get capabilities, try next one
                    continue

        # Default: Unknown tool
        return ToolCapabilities(tool="unknown")

    @beartype
    @require(lambda capabilities: capabilities.tool != "unknown", "Tool must be detected")
    @ensure(lambda result: isinstance(result, BridgeConfig), "Must return BridgeConfig")
    def auto_generate_bridge(
        self, capabilities: ToolCapabilities, bridge_config: BridgeConfig | None = None
    ) -> BridgeConfig:
        """
        Auto-generate bridge configuration based on detected capabilities using adapter registry.

        Args:
            capabilities: Detected tool capabilities
            bridge_config: Optional bridge configuration (for cross-repo support)

        Returns:
            Generated BridgeConfig instance

        Raises:
            ValueError: If adapter for detected tool is not registered
        """
        # Get adapter for detected tool
        if not AdapterRegistry.is_registered(capabilities.tool):
            msg = f"Adapter for tool '{capabilities.tool}' is not registered. Registered adapters: {', '.join(AdapterRegistry.list_adapters())}"
            raise ValueError(msg)

        adapter = AdapterRegistry.get_adapter(capabilities.tool)
        return adapter.generate_bridge_config(self.repo_path)

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

        # Suggest corrections based on common issues (adapter-agnostic)
        # Get adapter to check capabilities and provide adapter-specific suggestions
        adapter = AdapterRegistry.get_adapter(bridge_config.adapter.value)
        if adapter:
            adapter_capabilities = adapter.get_capabilities(self.repo_path, bridge_config)
            specs_dir = self.repo_path / adapter_capabilities.specs_dir

            # Check if specs directory exists but bridge points to different location
            if specs_dir.exists():
                for artifact in bridge_config.artifacts.values():
                    # Check if artifact pattern doesn't match detected specs_dir
                    if adapter_capabilities.specs_dir not in artifact.path_pattern:
                        suggestions.append(
                            f"Found '{adapter_capabilities.specs_dir}/' directory but bridge points to different pattern. "
                            f"Consider updating bridge config to use '{adapter_capabilities.specs_dir}/' pattern."
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
