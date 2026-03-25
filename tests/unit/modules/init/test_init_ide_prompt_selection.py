"""Tests for init ide prompt source catalog and --prompts parsing."""

from __future__ import annotations

from pathlib import Path

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


def test_discover_prompt_sources_catalog_includes_core_from_repo(tmp_path: Path) -> None:
    prompts = tmp_path / "resources" / "prompts"
    prompts.mkdir(parents=True)
    p1 = prompts / "specfact.01-import.md"
    p1.write_text("---\ndescription: A\n---\n# A\n", encoding="utf-8")

    catalog = discover_prompt_sources_catalog(tmp_path, include_package_fallback=False)

    assert PROMPT_SOURCE_CORE in catalog
    assert p1 in catalog[PROMPT_SOURCE_CORE]


def test_copy_prompts_by_source_to_ide_namespaces_by_source(tmp_path: Path) -> None:
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

    assert (tmp_path / ".cursor" / "commands" / "core" / "specfact.01-import.md") in copied
    assert (tmp_path / ".cursor" / "commands" / "nold-ai__specfact-backlog" / "specfact.backlog-add.md") in copied


def test_copy_prompts_by_source_to_ide_prunes_stale_in_selected_segment(tmp_path: Path) -> None:
    """Re-exporting a subset of core templates removes outputs that are no longer expected."""
    prompts = tmp_path / "resources" / "prompts"
    prompts.mkdir(parents=True)
    f1 = prompts / "specfact.01-import.md"
    f1.write_text("---\ndescription: A\n---\n# A\n", encoding="utf-8")
    f2 = prompts / "specfact.02-plan.md"
    f2.write_text("---\ndescription: B\n---\n# B\n", encoding="utf-8")

    core_dir = tmp_path / ".cursor" / "commands" / "core"
    copy_prompts_by_source_to_ide(tmp_path, "cursor", {PROMPT_SOURCE_CORE: [f1, f2]}, force=True)
    assert (core_dir / "specfact.01-import.md").is_file()
    assert (core_dir / "specfact.02-plan.md").is_file()

    copy_prompts_by_source_to_ide(tmp_path, "cursor", {PROMPT_SOURCE_CORE: [f1]}, force=True)
    assert (core_dir / "specfact.01-import.md").is_file()
    assert not (core_dir / "specfact.02-plan.md").exists()


def test_copy_prompts_by_source_to_ide_removes_unselected_catalog_segment(tmp_path: Path) -> None:
    """Selective export removes IDE segment dirs for catalog sources not in this run."""
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

    mod_seg = tmp_path / ".cursor" / "commands" / "nold-ai__specfact-backlog"
    copy_prompts_by_source_to_ide(
        tmp_path,
        "cursor",
        {PROMPT_SOURCE_CORE: [f1], "nold-ai/specfact-backlog": [f2]},
        force=True,
    )
    assert (mod_seg / "specfact.backlog-add.md").is_file()

    copy_prompts_by_source_to_ide(tmp_path, "cursor", {PROMPT_SOURCE_CORE: [f1]}, force=True)
    assert not mod_seg.exists()
    assert (tmp_path / ".cursor" / "commands" / "core" / "specfact.01-import.md").is_file()


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
