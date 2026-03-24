"""Tests for init resource resolution from installed module packages."""

from __future__ import annotations

from pathlib import Path

from specfact_cli.modules.init.src import commands as init_commands
from specfact_cli.utils import ide_setup


def test_resolve_field_mapping_templates_dir_prefers_installed_backlog_bundle(monkeypatch, tmp_path: Path) -> None:
    """Backlog field mapping templates should resolve from the installed backlog bundle."""
    installed_dir = tmp_path / "installed-backlog" / "resources" / "templates" / "backlog" / "field_mappings"
    installed_dir.mkdir(parents=True)
    (installed_dir / "ado_default.yaml").write_text("framework: default\n", encoding="utf-8")

    monkeypatch.setattr(
        init_commands,
        "_discover_module_resource_dirs",
        lambda resource_subpath, repo_path=None, categories=None: (
            [installed_dir.parent.parent.parent]
            if resource_subpath == "resources/templates/backlog/field_mappings" and categories == {"backlog"}
            else []
        ),
    )

    resolved = init_commands._resolve_field_mapping_templates_dir(tmp_path)

    assert resolved == installed_dir


def test_discover_prompt_template_files_uses_installed_module_resources(monkeypatch, tmp_path: Path) -> None:
    """Prompt discovery should source templates from installed module resources."""
    prompt_dir = tmp_path / "installed-codebase" / "resources" / "prompts"
    prompt_dir.mkdir(parents=True)
    prompt_file = prompt_dir / "specfact.04-sdd.md"
    prompt_file.write_text("---\ndescription: SDD\n---\n# SDD\n", encoding="utf-8")

    monkeypatch.setattr(
        ide_setup,
        "_discover_module_resource_dirs",
        lambda resource_subpath, repo_path=None, categories=None: (
            [prompt_dir.parent] if resource_subpath == "resources/prompts" else []
        ),
    )

    discovered = ide_setup.discover_prompt_template_files(tmp_path)

    assert discovered == [prompt_file]
