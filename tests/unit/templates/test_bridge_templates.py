"""Unit tests for bridge-based template loader."""



from specfact_cli.models.bridge import AdapterType, ArtifactMapping, BridgeConfig, TemplateMapping
from specfact_cli.templates.bridge_templates import BridgeTemplateLoader


class TestBridgeTemplateLoader:
    """Test BridgeTemplateLoader class."""

    def test_init_with_bridge_config(self, tmp_path):
        """Test BridgeTemplateLoader initialization with bridge config."""
        bridge_config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
            templates=TemplateMapping(
                root_dir=".specify/prompts",
                mapping={"specification": "specify.md", "plan": "plan.md"},
            ),
        )

        loader = BridgeTemplateLoader(tmp_path, bridge_config=bridge_config)
        assert loader.repo_path == tmp_path.resolve()
        assert loader.bridge_config == bridge_config

    def test_init_auto_detect(self, tmp_path):
        """Test BridgeTemplateLoader initialization with auto-detection."""
        # Create Spec-Kit structure with templates
        specify_dir = tmp_path / ".specify"
        specify_dir.mkdir()
        prompts_dir = specify_dir / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "specify.md").write_text("# Specify Template")
        (prompts_dir / "plan.md").write_text("# Plan Template")

        memory_dir = specify_dir / "memory"
        memory_dir.mkdir()
        specs_dir = tmp_path / "specs"
        specs_dir.mkdir()

        loader = BridgeTemplateLoader(tmp_path)
        assert loader.bridge_config is not None
        assert loader.bridge_config.adapter == AdapterType.SPECKIT

    def test_resolve_template_path(self, tmp_path):
        """Test resolving template path using bridge config."""
        bridge_config = BridgeConfig(
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

        loader = BridgeTemplateLoader(tmp_path, bridge_config=bridge_config)
        resolved = loader.resolve_template_path("specification")

        assert resolved == tmp_path / ".specify" / "prompts" / "specify.md"

    def test_resolve_template_path_not_found(self, tmp_path):
        """Test resolving template path for non-existent schema key."""
        bridge_config = BridgeConfig(
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

        loader = BridgeTemplateLoader(tmp_path, bridge_config=bridge_config)
        resolved = loader.resolve_template_path("tasks")

        assert resolved is None

    def test_load_template(self, tmp_path):
        """Test loading template from bridge config."""
        # Create template file
        prompts_dir = tmp_path / ".specify" / "prompts"
        prompts_dir.mkdir(parents=True)
        (prompts_dir / "specify.md").write_text("# Feature: {{ feature_title }}")

        bridge_config = BridgeConfig(
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

        loader = BridgeTemplateLoader(tmp_path, bridge_config=bridge_config)
        template = loader.load_template("specification")

        assert template is not None
        rendered = template.render(feature_title="Authentication")
        assert rendered == "# Feature: Authentication" or rendered == "# Feature: Authentication\n"

    def test_load_template_not_found(self, tmp_path):
        """Test loading template when file doesn't exist."""
        bridge_config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
            templates=TemplateMapping(
                root_dir=".specify/prompts",
                mapping={"specification": "nonexistent.md"},
            ),
        )

        loader = BridgeTemplateLoader(tmp_path, bridge_config=bridge_config)
        template = loader.load_template("specification")

        assert template is None

    def test_render_template(self, tmp_path):
        """Test rendering template with context."""
        # Create template file
        prompts_dir = tmp_path / ".specify" / "prompts"
        prompts_dir.mkdir(parents=True)
        (prompts_dir / "specify.md").write_text(
            "# Feature: {{ feature_title }}\n\nBundle: {{ bundle_name }}\nDate: {{ date }}"
        )

        bridge_config = BridgeConfig(
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

        loader = BridgeTemplateLoader(tmp_path, bridge_config=bridge_config)
        context = loader.create_template_context("FEATURE-001", "Authentication", "test-bundle")
        rendered = loader.render_template("specification", context)

        assert rendered is not None
        assert "Feature: Authentication" in rendered
        assert "Bundle: test-bundle" in rendered
        assert "date" in rendered.lower() or "Date:" in rendered

    def test_list_available_templates(self, tmp_path):
        """Test listing available templates."""
        bridge_config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
            templates=TemplateMapping(
                root_dir=".specify/prompts",
                mapping={"specification": "specify.md", "plan": "plan.md", "tasks": "tasks.md"},
            ),
        )

        loader = BridgeTemplateLoader(tmp_path, bridge_config=bridge_config)
        templates = loader.list_available_templates()

        assert "specification" in templates
        assert "plan" in templates
        assert "tasks" in templates
        assert len(templates) == 3

    def test_list_available_templates_no_config(self, tmp_path):
        """Test listing templates when no bridge templates configured."""
        bridge_config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
            templates=None,
        )

        loader = BridgeTemplateLoader(tmp_path, bridge_config=bridge_config)
        templates = loader.list_available_templates()

        assert len(templates) == 0

    def test_template_exists(self, tmp_path):
        """Test checking if template exists."""
        # Create template file
        prompts_dir = tmp_path / ".specify" / "prompts"
        prompts_dir.mkdir(parents=True)
        (prompts_dir / "specify.md").write_text("# Template")

        bridge_config = BridgeConfig(
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

        loader = BridgeTemplateLoader(tmp_path, bridge_config=bridge_config)
        assert loader.template_exists("specification") is True
        assert loader.template_exists("plan") is False

    def test_create_template_context(self, tmp_path):
        """Test creating template context."""
        bridge_config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
        )

        loader = BridgeTemplateLoader(tmp_path, bridge_config=bridge_config)
        context = loader.create_template_context(
            "FEATURE-001",
            "Authentication",
            "test-bundle",
            custom_var="custom_value",
        )

        assert context["feature_key"] == "FEATURE-001"
        assert context["feature_title"] == "Authentication"
        assert context["bundle_name"] == "test-bundle"
        assert context["custom_var"] == "custom_value"
        assert "date" in context
        assert "year" in context

    def test_fallback_to_default_templates(self, tmp_path):
        """Test fallback to default templates when bridge templates not configured."""
        bridge_config = BridgeConfig(
            adapter=AdapterType.SPECKIT,
            artifacts={
                "specification": ArtifactMapping(
                    path_pattern="specs/{feature_id}/spec.md",
                    format="markdown",
                ),
            },
            templates=None,
        )

        # Create default templates directory
        default_templates_dir = tmp_path / "resources" / "templates"
        default_templates_dir.mkdir(parents=True)
        (default_templates_dir / "spec.md").write_text("# Default Template")

        loader = BridgeTemplateLoader(tmp_path, bridge_config=bridge_config)
        # Should not error, but templates won't be available via bridge config
        assert loader.bridge_config is not None

