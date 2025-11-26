"""
Bridge-based template loader for dynamic template resolution.

This module provides functionality to load templates dynamically using bridge
configuration instead of hardcoded paths. Templates are resolved from bridge
config mappings, allowing users to customize templates or use different versions
without code changes.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from beartype import beartype
from icontract import ensure, require
from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound

from specfact_cli.models.bridge import BridgeConfig
from specfact_cli.sync.bridge_probe import BridgeProbe


class BridgeTemplateLoader:
    """
    Template loader that uses bridge configuration for dynamic template resolution.

    Loads templates from bridge-resolved paths instead of hardcoded directories.
    This allows users to customize templates or use different versions without
    code changes.
    """

    @beartype
    @require(lambda repo_path: repo_path.exists(), "Repository path must exist")
    @require(lambda repo_path: repo_path.is_dir(), "Repository path must be a directory")
    def __init__(self, repo_path: Path, bridge_config: BridgeConfig | None = None) -> None:
        """
        Initialize bridge template loader.

        Args:
            repo_path: Path to repository root
            bridge_config: Bridge configuration (auto-detected if None)
        """
        self.repo_path = Path(repo_path).resolve()
        self.bridge_config = bridge_config

        if self.bridge_config is None:
            # Auto-detect and load bridge config
            self.bridge_config = self._load_or_generate_bridge_config()

        # Initialize Jinja2 environment with bridge-resolved template directory
        self.env = self._create_jinja2_environment()

    @beartype
    @ensure(lambda result: isinstance(result, BridgeConfig), "Must return BridgeConfig")
    def _load_or_generate_bridge_config(self) -> BridgeConfig:
        """
        Load bridge config from file or auto-generate if missing.

        Returns:
            BridgeConfig instance
        """
        from specfact_cli.utils.structure import SpecFactStructure

        bridge_path = self.repo_path / SpecFactStructure.CONFIG / "bridge.yaml"

        if bridge_path.exists():
            return BridgeConfig.load_from_file(bridge_path)

        # Auto-generate bridge config
        probe = BridgeProbe(self.repo_path)
        capabilities = probe.detect()
        bridge_config = probe.auto_generate_bridge(capabilities)
        probe.save_bridge_config(bridge_config, overwrite=False)
        return bridge_config

    @beartype
    @ensure(lambda result: isinstance(result, Environment), "Must return Jinja2 Environment")
    def _create_jinja2_environment(self) -> Environment:
        """
        Create Jinja2 environment with bridge-resolved template directory.

        Returns:
            Jinja2 Environment instance
        """
        if self.bridge_config is None or self.bridge_config.templates is None:
            # Fallback to default template directory if no bridge templates configured
            default_templates_dir = self.repo_path / "resources" / "templates"
            if not default_templates_dir.exists():
                # Create empty environment if no templates found
                return Environment(loader=FileSystemLoader(str(self.repo_path)), trim_blocks=True, lstrip_blocks=True)
            return Environment(
                loader=FileSystemLoader(str(default_templates_dir)),
                trim_blocks=True,
                lstrip_blocks=True,
            )

        # Use bridge-resolved template root directory
        template_root = self.repo_path / self.bridge_config.templates.root_dir
        return Environment(
            loader=FileSystemLoader(str(template_root)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    @beartype
    @require(lambda schema_key: isinstance(schema_key, str) and len(schema_key) > 0, "Schema key must be non-empty")
    @ensure(lambda result: isinstance(result, Path) or result is None, "Must return Path or None")
    def resolve_template_path(self, schema_key: str) -> Path | None:
        """
        Resolve template path for a schema key using bridge configuration.

        Args:
            schema_key: Schema key (e.g., 'specification', 'plan', 'tasks')

        Returns:
            Resolved template Path object, or None if not found
        """
        if self.bridge_config is None or self.bridge_config.templates is None:
            return None

        try:
            return self.bridge_config.resolve_template_path(schema_key, base_path=self.repo_path)
        except ValueError:
            # Template not found in mapping
            return None

    @beartype
    @require(lambda schema_key: isinstance(schema_key, str) and len(schema_key) > 0, "Schema key must be non-empty")
    @ensure(lambda result: isinstance(result, Template) or result is None, "Must return Template or None")
    def load_template(self, schema_key: str) -> Template | None:
        """
        Load template for a schema key using bridge configuration.

        Args:
            schema_key: Schema key (e.g., 'specification', 'plan', 'tasks')

        Returns:
            Jinja2 Template object, or None if not found
        """
        if self.bridge_config is None or self.bridge_config.templates is None:
            return None

        # Get template file name from bridge mapping
        if schema_key not in self.bridge_config.templates.mapping:
            return None

        template_file = self.bridge_config.templates.mapping[schema_key]

        try:
            return self.env.get_template(template_file)
        except TemplateNotFound:
            return None

    @beartype
    @require(lambda schema_key: isinstance(schema_key, str) and len(schema_key) > 0, "Schema key must be non-empty")
    @require(lambda context: isinstance(context, dict), "Context must be dictionary")
    @ensure(lambda result: isinstance(result, str) or result is None, "Must return string or None")
    def render_template(self, schema_key: str, context: dict[str, str | int | float | bool | None]) -> str | None:
        """
        Render template for a schema key with provided context.

        Args:
            schema_key: Schema key (e.g., 'specification', 'plan', 'tasks')
            context: Template context variables (feature key, title, date, bundle name, etc.)

        Returns:
            Rendered template string, or None if template not found
        """
        template = self.load_template(schema_key)
        if template is None:
            return None

        try:
            return template.render(**context)
        except Exception:
            return None

    @beartype
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def list_available_templates(self) -> list[str]:
        """
        List all available templates from bridge configuration.

        Returns:
            List of schema keys for available templates
        """
        if self.bridge_config is None or self.bridge_config.templates is None:
            return []

        return list(self.bridge_config.templates.mapping.keys())

    @beartype
    @require(lambda schema_key: isinstance(schema_key, str) and len(schema_key) > 0, "Schema key must be non-empty")
    @ensure(lambda result: isinstance(result, bool), "Must return boolean")
    def template_exists(self, schema_key: str) -> bool:
        """
        Check if template exists for a schema key.

        Args:
            schema_key: Schema key (e.g., 'specification', 'plan', 'tasks')

        Returns:
            True if template exists, False otherwise
        """
        template_path = self.resolve_template_path(schema_key)
        return template_path is not None and template_path.exists()

    @beartype
    @require(lambda feature_key: isinstance(feature_key, str) and len(feature_key) > 0, "Feature key must be non-empty")
    @require(lambda feature_title: isinstance(feature_title, str), "Feature title must be string")
    @require(lambda bundle_name: isinstance(bundle_name, str) and len(bundle_name) > 0, "Bundle name must be non-empty")
    @ensure(lambda result: isinstance(result, dict), "Must return dictionary")
    def create_template_context(
        self,
        feature_key: str,
        feature_title: str,
        bundle_name: str,
        **kwargs: str | int | float | bool | None,
    ) -> dict[str, str | int | float | bool | None]:
        """
        Create template context with common variables.

        Args:
            feature_key: Feature key (e.g., 'FEATURE-001')
            feature_title: Feature title
            bundle_name: Project bundle name
            **kwargs: Additional context variables

        Returns:
            Dictionary with template context variables
        """
        context: dict[str, str | int | float | bool | None] = {
            "feature_key": feature_key,
            "feature_title": feature_title,
            "bundle_name": bundle_name,
            "date": datetime.now(UTC).isoformat(),
            "year": datetime.now(UTC).year,
        }

        # Add any additional context variables
        context.update(kwargs)

        return context
