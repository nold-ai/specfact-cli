"""Unit tests for bridge probe functionality."""


import pytest

from specfact_cli.models.bridge import AdapterType
from specfact_cli.sync.bridge_probe import BridgeProbe, ToolCapabilities


class TestToolCapabilities:
    """Test ToolCapabilities dataclass."""

    def test_create_tool_capabilities(self):
        """Test creating tool capabilities."""
        capabilities = ToolCapabilities(tool="speckit", version="0.0.85", layout="modern")
        assert capabilities.tool == "speckit"
        assert capabilities.version == "0.0.85"
        assert capabilities.layout == "modern"
        assert capabilities.specs_dir == "specs"  # Default value
        assert capabilities.has_external_config is False
        assert capabilities.has_custom_hooks is False


class TestBridgeProbe:
    """Test BridgeProbe class."""

    def test_init(self, tmp_path):
        """Test BridgeProbe initialization."""
        probe = BridgeProbe(tmp_path)
        assert probe.repo_path == tmp_path.resolve()

    def test_detect_unknown_tool(self, tmp_path):
        """Test detecting unknown tool (no Spec-Kit structure)."""
        probe = BridgeProbe(tmp_path)
        capabilities = probe.detect()
        assert capabilities.tool == "unknown"
        assert capabilities.version is None

    def test_detect_speckit_classic(self, tmp_path):
        """Test detecting Spec-Kit with classic layout."""
        # Create Spec-Kit structure
        specify_dir = tmp_path / ".specify"
        specify_dir.mkdir()
        memory_dir = specify_dir / "memory"
        memory_dir.mkdir()
        specs_dir = tmp_path / "specs"
        specs_dir.mkdir()

        probe = BridgeProbe(tmp_path)
        capabilities = probe.detect()

        assert capabilities.tool == "speckit"
        assert capabilities.layout == "classic"
        assert capabilities.specs_dir == "specs"

    def test_detect_speckit_modern(self, tmp_path):
        """Test detecting Spec-Kit with modern layout."""
        # Create Spec-Kit structure with modern layout
        specify_dir = tmp_path / ".specify"
        specify_dir.mkdir()
        memory_dir = specify_dir / "memory"
        memory_dir.mkdir()
        prompts_dir = specify_dir / "prompts"
        prompts_dir.mkdir()
        docs_specs_dir = tmp_path / "docs" / "specs"
        docs_specs_dir.mkdir(parents=True)

        probe = BridgeProbe(tmp_path)
        capabilities = probe.detect()

        assert capabilities.tool == "speckit"
        assert capabilities.layout == "modern"
        assert capabilities.specs_dir == "docs/specs"

    def test_detect_speckit_with_config(self, tmp_path):
        """Test detecting Spec-Kit with external config."""
        specify_dir = tmp_path / ".specify"
        specify_dir.mkdir()
        memory_dir = specify_dir / "memory"
        memory_dir.mkdir()
        config_file = specify_dir / "config.yaml"
        config_file.write_text("version: 1.0")

        probe = BridgeProbe(tmp_path)
        capabilities = probe.detect()

        assert capabilities.tool == "speckit"
        assert capabilities.has_external_config is True

    def test_detect_speckit_with_hooks(self, tmp_path):
        """Test detecting Spec-Kit with custom hooks."""
        specify_dir = tmp_path / ".specify"
        specify_dir.mkdir()
        memory_dir = specify_dir / "memory"
        memory_dir.mkdir()
        hooks_dir = specify_dir / "hooks"
        hooks_dir.mkdir()
        (hooks_dir / "pre-sync.sh").write_text("#!/bin/bash\necho 'pre-sync'")

        probe = BridgeProbe(tmp_path)
        capabilities = probe.detect()

        assert capabilities.tool == "speckit"
        assert capabilities.has_custom_hooks is True

    def test_auto_generate_bridge_speckit_classic(self, tmp_path):
        """Test auto-generating bridge config for Spec-Kit classic."""
        specify_dir = tmp_path / ".specify"
        specify_dir.mkdir()
        memory_dir = specify_dir / "memory"
        memory_dir.mkdir()
        specs_dir = tmp_path / "specs"
        specs_dir.mkdir()

        probe = BridgeProbe(tmp_path)
        capabilities = probe.detect()
        bridge_config = probe.auto_generate_bridge(capabilities)

        assert bridge_config.adapter == AdapterType.SPECKIT
        assert "specification" in bridge_config.artifacts
        assert "plan" in bridge_config.artifacts
        assert "tasks" in bridge_config.artifacts
        assert bridge_config.artifacts["specification"].path_pattern == "specs/{feature_id}/spec.md"

    def test_auto_generate_bridge_speckit_modern(self, tmp_path):
        """Test auto-generating bridge config for Spec-Kit modern."""
        specify_dir = tmp_path / ".specify"
        specify_dir.mkdir()
        memory_dir = specify_dir / "memory"
        memory_dir.mkdir()
        prompts_dir = specify_dir / "prompts"
        prompts_dir.mkdir()
        docs_specs_dir = tmp_path / "docs" / "specs"
        docs_specs_dir.mkdir(parents=True)

        probe = BridgeProbe(tmp_path)
        capabilities = probe.detect()
        bridge_config = probe.auto_generate_bridge(capabilities)

        assert bridge_config.adapter == AdapterType.SPECKIT
        assert bridge_config.artifacts["specification"].path_pattern == "docs/specs/{feature_id}/spec.md"

    def test_auto_generate_bridge_with_templates(self, tmp_path):
        """Test auto-generating bridge config with template mappings."""
        specify_dir = tmp_path / ".specify"
        specify_dir.mkdir()
        memory_dir = specify_dir / "memory"
        memory_dir.mkdir()
        prompts_dir = specify_dir / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "specify.md").write_text("# Specify template")
        (prompts_dir / "plan.md").write_text("# Plan template")

        probe = BridgeProbe(tmp_path)
        capabilities = probe.detect()
        bridge_config = probe.auto_generate_bridge(capabilities)

        assert bridge_config.templates is not None
        assert "specification" in bridge_config.templates.mapping
        assert "plan" in bridge_config.templates.mapping

    def test_auto_generate_bridge_unknown(self, tmp_path):
        """Test auto-generating bridge config for unknown tool."""
        probe = BridgeProbe(tmp_path)
        capabilities = ToolCapabilities(tool="unknown")
        bridge_config = probe.auto_generate_bridge(capabilities)

        assert bridge_config.adapter == AdapterType.GENERIC_MARKDOWN
        assert "specification" in bridge_config.artifacts

    def test_validate_bridge_no_errors(self, tmp_path):
        """Test validating bridge config with no errors."""
        # Create Spec-Kit structure with sample feature
        specs_dir = tmp_path / "specs"
        specs_dir.mkdir()
        feature_dir = specs_dir / "001-auth"
        feature_dir.mkdir()
        (feature_dir / "spec.md").write_text("# Auth Feature")
        (feature_dir / "plan.md").write_text("# Auth Plan")

        from specfact_cli.models.bridge import ArtifactMapping, BridgeConfig

        bridge_config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )

        probe = BridgeProbe(tmp_path)
        results = probe.validate_bridge(bridge_config)

        assert len(results["errors"]) == 0
        # May have warnings if not all sample feature IDs are found, which is normal

    def test_validate_bridge_with_suggestions(self, tmp_path):
        """Test validating bridge config with suggestions."""
        # Create classic specs/ directory
        specs_dir = tmp_path / "specs"
        specs_dir.mkdir()

        # But bridge points to docs/specs/
        from specfact_cli.models.bridge import ArtifactMapping, BridgeConfig

        bridge_config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="docs/specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )

        probe = BridgeProbe(tmp_path)
        results = probe.validate_bridge(bridge_config)

        # Should suggest using specs/ instead of docs/specs/
        assert len(results["suggestions"]) > 0
        assert any("specs/" in suggestion for suggestion in results["suggestions"])

    def test_save_bridge_config(self, tmp_path):
        """Test saving bridge config to file."""
        from specfact_cli.models.bridge import ArtifactMapping, BridgeConfig

        bridge_config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )

        probe = BridgeProbe(tmp_path)
        probe.save_bridge_config(bridge_config)

        bridge_path = tmp_path / ".specfact" / "config" / "bridge.yaml"
        assert bridge_path.exists()

        # Verify it can be loaded back
        loaded = BridgeConfig.load_from_file(bridge_path)
        assert loaded.adapter == AdapterType.SPECKIT

    def test_save_bridge_config_overwrite(self, tmp_path):
        """Test saving bridge config with overwrite."""
        from specfact_cli.models.bridge import ArtifactMapping, BridgeConfig

        bridge_config1 = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )

        bridge_config2 = BridgeConfig(
            adapter=AdapterType.GENERIC_MARKDOWN,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="docs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )

        probe = BridgeProbe(tmp_path)
        probe.save_bridge_config(bridge_config1)
        probe.save_bridge_config(bridge_config2, overwrite=True)

        bridge_path = tmp_path / ".specfact" / "config" / "bridge.yaml"
        loaded = BridgeConfig.load_from_file(bridge_path)
        assert loaded.adapter == AdapterType.GENERIC_MARKDOWN

    def test_save_bridge_config_no_overwrite_error(self, tmp_path):
        """Test that saving without overwrite raises error if file exists."""
        from specfact_cli.models.bridge import ArtifactMapping, BridgeConfig

        bridge_config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )

        probe = BridgeProbe(tmp_path)
        probe.save_bridge_config(bridge_config)

        # Try to save again without overwrite
        with pytest.raises(FileExistsError):
            probe.save_bridge_config(bridge_config, overwrite=False)

