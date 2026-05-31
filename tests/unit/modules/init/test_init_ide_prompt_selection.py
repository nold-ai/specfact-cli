"""Tests for init ide prompt source catalog and --prompts parsing."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.modules.init.src import commands as init_commands
from specfact_cli.utils.ide_setup import (
    PROMPT_SOURCE_CORE,
    copy_prompts_by_source_to_ide,
    discover_prompt_sources_catalog,
    source_id_to_path_segment,
)


def test_source_id_to_path_segment_sanitizes_slashes() -> None:
    assert source_id_to_path_segment("nold-ai/specfact-backlog") == "nold-ai__specfact-backlog"
    assert source_id_to_path_segment("core") == "core"


def test_discover_prompt_sources_catalog_includes_core_from_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import specfact_cli.utils.ide_setup as ide_setup_module

    monkeypatch.setattr(ide_setup_module, "_module_prompt_sources_catalog", lambda _rp: {})

    prompts = tmp_path / "resources" / "prompts"
    prompts.mkdir(parents=True)
    p1 = prompts / "specfact.01-import.md"
    p1.write_text("---\ndescription: A\n---\n# A\n", encoding="utf-8")

    catalog = discover_prompt_sources_catalog(tmp_path, include_package_fallback=False)

    assert PROMPT_SOURCE_CORE in catalog
    assert p1 in catalog[PROMPT_SOURCE_CORE]


def test_discover_prompt_sources_catalog_omits_core_when_module_has_same_basename(tmp_path: Path) -> None:
    core = tmp_path / "resources" / "prompts"
    core.mkdir(parents=True)
    p_core = core / "specfact.01-import.md"
    p_core.write_text("---\n---\n# core\n", encoding="utf-8")

    package_dir = tmp_path / ".specfact" / "modules" / "specfact-codebase"
    prompt_dir = package_dir / "resources" / "prompts"
    prompt_dir.mkdir(parents=True)
    (package_dir / "module-package.yaml").write_text(
        "name: nold-ai/specfact-codebase\nversion: '0.1.0'\ncommands: [codebase]\ncategory: codebase\n"
        "bundle_group_command: code\n",
        encoding="utf-8",
    )
    p_mod = prompt_dir / "specfact.01-import.md"
    p_mod.write_text("---\n---\n# mod\n", encoding="utf-8")

    catalog = discover_prompt_sources_catalog(tmp_path, include_package_fallback=False)

    assert PROMPT_SOURCE_CORE not in catalog
    assert "nold-ai/specfact-codebase" in catalog
    assert p_mod in catalog["nold-ai/specfact-codebase"]


def test_copy_prompts_by_source_to_ide_exports_flat_under_ide_root(tmp_path: Path) -> None:
    prompts = tmp_path / "resources" / "prompts"
    prompts.mkdir(parents=True)
    f1 = prompts / "specfact.01-import.md"
    f1.write_text("---\ndescription: A\n---\n# A\n", encoding="utf-8")

    mod_dir = tmp_path / "mod" / "resources" / "prompts"
    mod_dir.mkdir(parents=True)
    f2 = mod_dir / "specfact.backlog-add.md"
    f2.write_text("---\ndescription: B\n---\n# B\n", encoding="utf-8")

    by_source = {PROMPT_SOURCE_CORE: [f1], "nold-ai/specfact-backlog": [f2]}
    copied, _settings = copy_prompts_by_source_to_ide(tmp_path, "cursor", by_source, force=True)

    cmd = tmp_path / ".cursor" / "commands"
    assert (cmd / "specfact.01-import.md") in copied
    assert (cmd / "specfact.backlog-add.md") in copied
    assert not (cmd / "core").exists()


def test_copy_prompts_by_source_to_ide_prunes_stale_in_flat_export(tmp_path: Path) -> None:
    """Re-exporting a subset of core templates removes outputs that are no longer expected."""
    prompts = tmp_path / "resources" / "prompts"
    prompts.mkdir(parents=True)
    f1 = prompts / "specfact.01-import.md"
    f1.write_text("---\ndescription: A\n---\n# A\n", encoding="utf-8")
    f2 = prompts / "specfact.02-plan.md"
    f2.write_text("---\ndescription: B\n---\n# B\n", encoding="utf-8")

    cmd_dir = tmp_path / ".cursor" / "commands"
    copy_prompts_by_source_to_ide(tmp_path, "cursor", {PROMPT_SOURCE_CORE: [f1, f2]}, force=True)
    assert (cmd_dir / "specfact.01-import.md").is_file()
    assert (cmd_dir / "specfact.02-plan.md").is_file()

    copy_prompts_by_source_to_ide(tmp_path, "cursor", {PROMPT_SOURCE_CORE: [f1]}, force=True)
    assert (cmd_dir / "specfact.01-import.md").is_file()
    assert not (cmd_dir / "specfact.02-plan.md").exists()


def test_copy_prompts_by_source_to_ide_removes_unselected_module_exports_from_flat(tmp_path: Path) -> None:
    """Selective export removes flat outputs from catalog sources not in this run."""
    prompts = tmp_path / "resources" / "prompts"
    prompts.mkdir(parents=True)
    f1 = prompts / "specfact.01-import.md"
    f1.write_text("---\ndescription: A\n---\n# A\n", encoding="utf-8")

    package_dir = tmp_path / ".specfact" / "modules" / "specfact-backlog"
    prompt_dir = package_dir / "resources" / "prompts"
    prompt_dir.mkdir(parents=True)
    (package_dir / "module-package.yaml").write_text(
        "name: nold-ai/specfact-backlog\nversion: '0.1.0'\ncommands: [backlog]\ncategory: backlog\n"
        "bundle_group_command: backlog\n",
        encoding="utf-8",
    )
    f2 = prompt_dir / "specfact.backlog-add.md"
    f2.write_text("---\ndescription: B\n---\n# B\n", encoding="utf-8")

    cmd_dir = tmp_path / ".cursor" / "commands"
    copy_prompts_by_source_to_ide(
        tmp_path,
        "cursor",
        {PROMPT_SOURCE_CORE: [f1], "nold-ai/specfact-backlog": [f2]},
        force=True,
    )
    assert (cmd_dir / "specfact.backlog-add.md").is_file()

    copy_prompts_by_source_to_ide(tmp_path, "cursor", {PROMPT_SOURCE_CORE: [f1]}, force=True)
    assert (cmd_dir / "specfact.01-import.md").is_file()
    assert not (cmd_dir / "specfact.backlog-add.md").exists()


def test_copy_prompts_by_source_to_codex_exports_grouped_skills(tmp_path: Path) -> None:
    """Codex receives capability-oriented skills grouped by source/module."""
    prompts = tmp_path / "resources" / "prompts"
    prompts.mkdir(parents=True)
    f1 = prompts / "specfact.01-import.md"
    f1.write_text("---\ndescription: A\n---\n# A\n", encoding="utf-8")
    f2 = prompts / "specfact.validate.md"
    f2.write_text("---\ndescription: B\n---\n# B\n", encoding="utf-8")

    mod_dir = tmp_path / "mod" / "resources" / "prompts"
    mod_dir.mkdir(parents=True)
    f3 = mod_dir / "specfact.backlog-add.md"
    f3.write_text("---\ndescription: C\n---\n# C\n", encoding="utf-8")

    copied, _settings = copy_prompts_by_source_to_ide(
        tmp_path,
        "codex",
        {PROMPT_SOURCE_CORE: [f1, f2], "nold-ai/specfact-backlog": [f3]},
        force=True,
    )

    skills_dir = tmp_path / ".codex" / "skills"
    assert copied == [
        skills_dir / "specfact-cli" / "SKILL.md",
        skills_dir / "specfact-backlog" / "SKILL.md",
    ]
    assert not (skills_dir / "specfact.01-import").exists()
    core_skill = (skills_dir / "specfact-cli" / "SKILL.md").read_text(encoding="utf-8")
    module_skill = (skills_dir / "specfact-backlog" / "SKILL.md").read_text(encoding="utf-8")
    assert "## specfact.01-import" in core_skill
    assert "## specfact.validate" in core_skill
    assert "## specfact.backlog-add" in module_skill


def test_copy_prompts_by_source_to_codex_prunes_stale_per_prompt_skill_exports(tmp_path: Path) -> None:
    """A grouped skill export removes stale per-prompt skill folders from earlier previews."""
    prompts = tmp_path / "resources" / "prompts"
    prompts.mkdir(parents=True)
    f1 = prompts / "specfact.01-import.md"
    f1.write_text("---\ndescription: A\n---\n# A\n", encoding="utf-8")

    stale = tmp_path / ".codex" / "skills" / "specfact.01-import" / "SKILL.md"
    stale.parent.mkdir(parents=True)
    stale.write_text("stale\n", encoding="utf-8")
    owned = tmp_path / ".codex" / "skills" / "openspec-workflows" / "SKILL.md"
    owned.parent.mkdir(parents=True)
    owned.write_text("owned\n", encoding="utf-8")

    copy_prompts_by_source_to_ide(tmp_path, "codex", {PROMPT_SOURCE_CORE: [f1]}, force=True)

    assert not stale.exists()
    assert not stale.parent.exists()
    assert owned.exists()
    assert (tmp_path / ".codex" / "skills" / "specfact-cli" / "SKILL.md").exists()


def test_parse_prompts_option_all_expands_to_full_catalog() -> None:
    fake_catalog = {
        PROMPT_SOURCE_CORE: [],
        "nold-ai/x": [],
    }
    out = init_commands._parse_prompts_option_to_catalog(fake_catalog, "all")
    assert set(out.keys()) == {PROMPT_SOURCE_CORE, "nold-ai/x"}


def test_parse_prompts_option_core_token(tmp_path: Path) -> None:
    p = tmp_path / "specfact.01-import.md"
    p.write_text("---\n---\n", encoding="utf-8")
    cat = {PROMPT_SOURCE_CORE: [p]}
    out = init_commands._parse_prompts_option_to_catalog(cat, "core")
    assert out == {PROMPT_SOURCE_CORE: [p]}


def test_init_ide_malformed_vscode_settings_exits_nonzero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import specfact_cli.utils.ide_setup as ide_setup_module

    monkeypatch.setattr(ide_setup_module, "_module_prompt_sources_catalog", lambda _rp: {})
    prompts = tmp_path / "resources" / "prompts"
    prompts.mkdir(parents=True)
    (prompts / "specfact.01-import.md").write_text("---\ndescription: A\n---\n# A\n", encoding="utf-8")

    vscode_dir = tmp_path / ".vscode"
    vscode_dir.mkdir(parents=True)
    malformed = "{not-json"
    (vscode_dir / "settings.json").write_text(malformed, encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["init", "ide", "--repo", str(tmp_path), "--ide", "vscode", "--prompts", "core"],
    )
    assert result.exit_code == 1
    assert "invalid json" in result.stdout.lower() or "cannot merge" in result.stdout.lower()
    assert (vscode_dir / "settings.json").read_text(encoding="utf-8") == malformed


def test_init_ide_invalid_prompts_token_exits_nonzero(tmp_path: Path) -> None:
    prompts = tmp_path / "resources" / "prompts"
    prompts.mkdir(parents=True)
    (prompts / "specfact.01-import.md").write_text("---\ndescription: A\n---\n# A\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["init", "ide", "--repo", str(tmp_path), "--ide", "cursor", "--prompts", "nold-ai/not-installed", "--force"],
    )
    assert result.exit_code == 1
    out = result.stdout.lower()
    assert "not available" in out
    assert "nold-ai/not-installed" in result.stdout
