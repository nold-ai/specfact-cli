"""Unit tests for bridge configuration models."""

from pathlib import Path

import pytest

from specfact_cli.models.bridge import (
    AdapterType,
    ArtifactMapping,
    BridgeConfig,
    CommandMapping,
    TemplateMapping,
)


class TestArtifactMapping:
    """Test ArtifactMapping model."""

    def test_create_artifact_mapping(self):
        """Test creating artifact mapping."""
        mapping = ArtifactMapping(
            path_pattern="specs/{feature_id}/spec.md",
            format="markdown",
        )
        assert mapping.path_pattern == "specs/{feature_id}/spec.md"
        assert mapping.format == "markdown"
        assert mapping.sync_target is None

    def test_create_artifact_mapping_with_sync_target(self):
        """Test creating artifact mapping with sync target."""
        mapping = ArtifactMapping(
            path_pattern="specs/{feature_id}/tasks.md",
            format="markdown",
            sync_target="github_issues",
        )
        assert mapping.sync_target == "github_issues"

    def test_resolve_path(self, tmp_path):
        """Test resolving path with context."""
        mapping = ArtifactMapping(
            path_pattern="specs/{feature_id}/spec.md",
            format="markdown",
        )
        context = {"feature_id": "001-auth"}
        resolved = mapping.resolve_path(context, base_path=tmp_path)
        assert resolved == tmp_path / "specs" / "001-auth" / "spec.md"

    def test_resolve_path_missing_context(self):
        """Test resolving path with missing context variable."""
        mapping = ArtifactMapping(
            path_pattern="specs/{feature_id}/spec.md",
            format="markdown",
        )
        context = {}  # Missing feature_id
        with pytest.raises(ValueError, match="Missing context variable"):
            mapping.resolve_path(context)

    def test_resolve_path_empty_pattern(self):
        """Test that empty path pattern is rejected."""
        # Pydantic doesn't validate empty strings for required fields by default
        # The contract decorator will catch this at runtime
        mapping = ArtifactMapping(path_pattern="", format="markdown")
        # Contract will fail when resolve_path is called
        with pytest.raises((ValueError, Exception), match="Path pattern must not be empty"):
            mapping.resolve_path({})


class TestCommandMapping:
    """Test CommandMapping model."""

    def test_create_command_mapping(self):
        """Test creating command mapping."""
        mapping = CommandMapping(
            trigger="/speckit.specify",
            input_ref="specification",
        )
        assert mapping.trigger == "/speckit.specify"
        assert mapping.input_ref == "specification"
        assert mapping.output_ref is None

    def test_create_command_mapping_with_output(self):
        """Test creating command mapping with output reference."""
        mapping = CommandMapping(
            trigger="/speckit.plan",
            input_ref="specification",
            output_ref="plan",
        )
        assert mapping.output_ref == "plan"


class TestTemplateMapping:
    """Test TemplateMapping model."""

    def test_create_template_mapping(self):
        """Test creating template mapping."""
        mapping = TemplateMapping(
            root_dir=".specify/prompts",
            mapping={"specification": "specify.md", "plan": "plan.md"},
        )
        assert mapping.root_dir == ".specify/prompts"
        assert mapping.mapping["specification"] == "specify.md"

    def test_resolve_template_path(self, tmp_path):
        """Test resolving template path."""
        mapping = TemplateMapping(
            root_dir=".specify/prompts",
            mapping={"specification": "specify.md"},
        )
        resolved = mapping.resolve_template_path("specification", base_path=tmp_path)
        assert resolved == tmp_path / ".specify" / "prompts" / "specify.md"

    def test_resolve_template_path_missing_key(self, tmp_path):
        """Test resolving template path with missing key."""
        mapping = TemplateMapping(
            root_dir=".specify/prompts",
            mapping={"specification": "specify.md"},
        )
        with pytest.raises(ValueError, match="not found in template mapping"):
            mapping.resolve_template_path("plan", base_path=tmp_path)


class TestBridgeConfig:
    """Test BridgeConfig model."""

    def test_create_bridge_config(self):
        """Test creating bridge config."""
        config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )
        assert config.version == "1.0"
        assert config.adapter == AdapterType.SPECKIT
        assert "specification" in config.artifacts
        assert config.commands == {}
        assert config.templates is None

    def test_create_bridge_config_with_all_fields(self):
        """Test creating bridge config with all fields."""
        config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
            commands={
                "analyze": CommandMapping(
                    trigger="/speckit.specify",
                    input_ref="specification",
                ),
            },
            templates=TemplateMapping(
                root_dir=".specify/prompts",
                mapping={"specification": "specify.md"},
            ),
        )
        assert len(config.commands) == 1
        assert config.templates is not None

    def test_resolve_path(self, tmp_path):
        """Test resolving artifact path."""
        config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )
        context = {"feature_id": "001-auth"}
        resolved = config.resolve_path("specification", context, base_path=tmp_path)
        assert resolved == tmp_path / "specs" / "001-auth" / "spec.md"

    def test_resolve_path_missing_artifact(self, tmp_path):
        """Test resolving path with missing artifact key."""
        config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )
        with pytest.raises((ValueError, Exception), match=r"Artifact key must exist|not found"):
            config.resolve_path("plan", {}, base_path=tmp_path)

    def test_get_command(self):
        """Test getting command mapping."""
        config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
            commands={
                "analyze": CommandMapping(
                    trigger="/speckit.specify",
                    input_ref="specification",
                ),
            },
        )
        command = config.get_command("analyze")
        assert command.trigger == "/speckit.specify"

    def test_get_command_missing(self):
        """Test getting command with missing key."""
        config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )
        with pytest.raises((ValueError, Exception), match=r"Command key must exist|not found"):
            config.get_command("analyze")

    def test_resolve_template_path(self, tmp_path):
        """Test resolving template path."""
        config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
            templates=TemplateMapping(
                root_dir=".specify/prompts",
                mapping={"specification": "specify.md"},
            ),
        )
        resolved = config.resolve_template_path("specification", base_path=tmp_path)
        assert resolved == tmp_path / ".specify" / "prompts" / "specify.md"

    def test_resolve_template_path_no_templates(self, tmp_path):
        """Test resolving template path when templates not configured."""
        config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )
        with pytest.raises((ValueError, Exception), match=r"Templates not configured|must be configured"):
            config.resolve_template_path("specification", base_path=tmp_path)

    def test_load_from_file(self, tmp_path):
        """Test loading bridge config from file."""
        config_path = tmp_path / "bridge.yaml"
        config_data = {
            "version": "1.0",
            "adapter": "speckit",
            "artifacts": {
                "specification": {
                    "path_pattern": "specs/{feature_id}/spec.md",
                    "format": "markdown",
                },
            },
        }
        from specfact_cli.utils.structured_io import StructuredFormat, dump_structured_file

        dump_structured_file(config_data, config_path, StructuredFormat.YAML)

        loaded = BridgeConfig.load_from_file(config_path)
        assert loaded.adapter == AdapterType.SPECKIT
        assert "specification" in loaded.artifacts

    def test_save_to_file(self, tmp_path):
        """Test saving bridge config to file."""
        config_path = tmp_path / "bridge.yaml"
        config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )
        config.save_to_file(config_path)
        assert config_path.exists()

        # Verify it can be loaded back
        loaded = BridgeConfig.load_from_file(config_path)
        assert loaded.adapter == AdapterType.SPECKIT
        assert "specification" in loaded.artifacts

    def test_load_from_file_nonexistent(self):
        """Test loading from nonexistent file."""
        with pytest.raises((ValueError, FileNotFoundError, Exception)):
            BridgeConfig.load_from_file(Path("/nonexistent/bridge.yaml"))


class TestAdapterType:
    """Test AdapterType enum."""

    def test_adapter_types(self):
        """Test all adapter types."""
        assert AdapterType.SPECKIT == "speckit"
        assert AdapterType.GENERIC_MARKDOWN == "generic-markdown"
        assert AdapterType.LINEAR == "linear"
        assert AdapterType.JIRA == "jira"
        assert AdapterType.NOTION == "notion"


class TestBridgeConfigPresets:
    """Test BridgeConfig preset methods."""

    def test_preset_speckit_classic(self):
        """Test Spec-Kit classic preset."""
        config = BridgeConfig.preset_speckit_classic()
        assert config.adapter == AdapterType.SPECKIT
        assert "specification" in config.artifacts
        assert config.artifacts["specification"].path_pattern == "specs/{feature_id}/spec.md"
        assert "plan" in config.artifacts
        assert "tasks" in config.artifacts
        assert "contracts" in config.artifacts
        assert len(config.commands) == 2
        assert config.templates is not None
        assert config.templates.root_dir == ".specify/prompts"

    def test_preset_speckit_modern(self):
        """Test Spec-Kit modern preset."""
        config = BridgeConfig.preset_speckit_modern()
        assert config.adapter == AdapterType.SPECKIT
        assert "specification" in config.artifacts
        assert config.artifacts["specification"].path_pattern == "docs/specs/{feature_id}/spec.md"
        assert "plan" in config.artifacts
        assert "tasks" in config.artifacts
        assert "contracts" in config.artifacts
        assert len(config.commands) == 2
        assert config.templates is not None

    def test_preset_generic_markdown(self):
        """Test generic markdown preset."""
        config = BridgeConfig.preset_generic_markdown()
        assert config.adapter == AdapterType.GENERIC_MARKDOWN
        assert "specification" in config.artifacts
        assert config.artifacts["specification"].path_pattern == "specs/{feature_id}/spec.md"
        assert len(config.commands) == 0
        assert config.templates is None

    def test_preset_speckit_classic_resolve_path(self, tmp_path):
        """Test that preset paths can be resolved."""
        config = BridgeConfig.preset_speckit_classic()
        context = {"feature_id": "001-auth"}
        resolved = config.resolve_path("specification", context, base_path=tmp_path)
        assert resolved == tmp_path / "specs" / "001-auth" / "spec.md"

    def test_preset_speckit_modern_resolve_path(self, tmp_path):
        """Test that modern preset paths can be resolved."""
        config = BridgeConfig.preset_speckit_modern()
        context = {"feature_id": "001-auth"}
        resolved = config.resolve_path("specification", context, base_path=tmp_path)
        assert resolved == tmp_path / "docs" / "specs" / "001-auth" / "spec.md"
