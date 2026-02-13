"""Unit tests for backlog-core schema extension access patterns."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml


# ruff: noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "modules" / "backlog-core" / "src"))
sys.path.insert(0, str(REPO_ROOT / "src"))

from backlog_core.graph.config_schema import load_backlog_config_from_spec
from backlog_core.graph.models import BacklogGraph

from specfact_cli.models.plan import Product
from specfact_cli.models.project import BundleManifest, ProjectBundle, ProjectMetadata


def test_module_package_declares_backlog_core_schema_extensions() -> None:
    """module-package.yaml declares project metadata and bundle schema extensions."""
    module_package = REPO_ROOT / "modules" / "backlog-core" / "module-package.yaml"
    data = yaml.safe_load(module_package.read_text(encoding="utf-8"))
    schema_extensions = data.get("schema_extensions", {})

    assert "project_bundle" in schema_extensions
    assert "project_metadata" in schema_extensions
    assert "backlog_core.backlog_graph" in schema_extensions["project_bundle"]
    assert "backlog_core.backlog_config" in schema_extensions["project_metadata"]


def test_project_metadata_extension_roundtrip_via_bundle_save_load(tmp_path: Path) -> None:
    """ProjectMetadata extension values persist through bundle serialization."""
    bundle_dir = tmp_path / ".specfact" / "projects" / "schema-extension-bundle"
    metadata = ProjectMetadata(stability="alpha")
    metadata.set_extension(
        "backlog_core",
        "backlog_config",
        {"adapter": "github", "project_id": "nold-ai/specfact-cli", "template": "github_projects"},
    )
    bundle = ProjectBundle(
        manifest=BundleManifest(schema_metadata=None, project_metadata=metadata),
        bundle_name="schema-extension-bundle",
        product=Product(themes=["Schema"]),
    )

    bundle.save_to_directory(bundle_dir)
    loaded = ProjectBundle.load_from_directory(bundle_dir)
    loaded_metadata = loaded.manifest.project_metadata

    assert loaded_metadata is not None
    cfg = loaded_metadata.get_extension("backlog_core", "backlog_config")
    assert isinstance(cfg, dict)
    assert cfg["adapter"] == "github"
    assert cfg["project_id"] == "nold-ai/specfact-cli"


def test_backlog_graph_json_serialization_roundtrip() -> None:
    """BacklogGraph supports stable to_json/from_json serialization."""
    graph = BacklogGraph(provider="github", project_key="nold-ai/specfact-cli")
    payload = graph.to_json()
    restored = BacklogGraph.from_json(payload)

    assert restored.provider == "github"
    assert restored.project_key == "nold-ai/specfact-cli"


def test_load_backlog_config_from_spec_supports_backlog_config(tmp_path: Path) -> None:
    """Spec config loader reads backlog_config section from .specfact/spec.yaml."""
    spec_path = tmp_path / ".specfact" / "spec.yaml"
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(
        """
backlog_config:
  dependencies:
    template: github_projects
  providers:
    github:
      adapter: github
      project_id: nold-ai/specfact-cli
""".strip(),
        encoding="utf-8",
    )

    cfg = load_backlog_config_from_spec(spec_path)

    assert cfg is not None
    assert cfg.dependencies.template == "github_projects"
    assert cfg.providers["github"].project_id == "nold-ai/specfact-cli"


def test_load_backlog_config_from_spec_supports_devops_stages(tmp_path: Path) -> None:
    """Spec config loader accepts devops_stages section for workflow defaults."""
    spec_path = tmp_path / ".specfact" / "spec.yaml"
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(
        """
backlog_config:
  dependencies:
    template: github_projects
devops_stages:
  plan:
    default_action: generate-roadmap
  monitor:
    default_action: health-check
""".strip(),
        encoding="utf-8",
    )

    cfg = load_backlog_config_from_spec(spec_path)

    assert cfg is not None
    assert cfg.devops_stages["plan"].default_action == "generate-roadmap"
    assert cfg.devops_stages["monitor"].default_action == "health-check"
