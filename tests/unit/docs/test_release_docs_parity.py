from __future__ import annotations

from pathlib import Path


def _repo_file(path: str) -> Path:
    return Path(__file__).resolve().parents[3] / path


def test_changelog_has_single_0340_release_header() -> None:
    changelog = _repo_file("CHANGELOG.md").read_text(encoding="utf-8")
    assert changelog.count("## [0.34.0] - 2026-02-18") == 1


def test_patch_mode_is_not_left_under_unreleased() -> None:
    changelog = _repo_file("CHANGELOG.md").read_text(encoding="utf-8")
    unreleased_start = changelog.find("## [Unreleased]")
    next_release_start = changelog.find("\n## [", unreleased_start + 1)
    unreleased_block = changelog[unreleased_start:next_release_start]
    assert "Patch mode module" not in unreleased_block


def test_command_reference_documents_patch_apply() -> None:
    commands_doc = _repo_file("docs/reference/commands.md").read_text(encoding="utf-8")
    assert "specfact govern patch" in commands_doc


def test_module_bootstrap_checklist_uses_current_bundle_ids() -> None:
    checklist = _repo_file("docs/getting-started/module-bootstrap-checklist.md").read_text(encoding="utf-8")
    assert "specfact module install backlog --source bundled" in checklist
    assert "backlog-core" not in checklist


def test_module_publishing_docs_describe_modules_repo_flow() -> None:
    publishing = _repo_file("docs/guides/publishing-modules.md").read_text(encoding="utf-8")
    assert "specfact-cli-modules" in publishing
    assert "Push to `dev` and `main`" in publishing
    assert "tags matching `*-v*`" not in publishing


def test_module_contracts_reference_external_bundle_boundary() -> None:
    contracts_doc = _repo_file("docs/reference/module-contracts.md").read_text(encoding="utf-8")
    assert "specfact-cli-modules" in contracts_doc
    assert "Core runtime must not import external bundle package namespaces" in contracts_doc


def test_readme_and_docs_index_define_core_and_modules_split() -> None:
    readme = _repo_file("README.md").read_text(encoding="utf-8")
    docs_index = _repo_file("docs/index.md").read_text(encoding="utf-8")
    assert "canonical docs entry point" in readme
    assert "module-specific deep docs are canonically owned by `specfact-cli-modules`" in readme
    assert "https://modules.specfact.io/" in readme
    assert "Docs Home" in docs_index
    assert "Core CLI" in docs_index
    assert "Modules" in docs_index


def test_top_navigation_exposes_docs_home_core_cli_and_modules() -> None:
    layout = _repo_file("docs/_layouts/default.html").read_text(encoding="utf-8")
    assert ">Docs Home<" in layout
    assert ">Core CLI<" in layout
    assert ">Modules<" in layout
    assert "https://modules.specfact.io/" in layout


def test_command_reference_and_docs_readme_link_to_modules_canonical_site() -> None:
    docs_readme = _repo_file("docs/README.md").read_text(encoding="utf-8")
    commands_doc = _repo_file("docs/reference/commands.md").read_text(encoding="utf-8")
    assert "canonical modules docs site" in docs_readme
    assert "https://modules.specfact.io/" in docs_readme
    assert "canonical modules docs site" in commands_doc
    assert "https://modules.specfact.io/" in commands_doc


def test_bundle_focused_pages_use_handoff_note_instead_of_future_migration_language() -> None:
    backlog_refinement = _repo_file("docs/guides/backlog-refinement.md").read_text(encoding="utf-8")
    github_adapter = _repo_file("docs/adapters/github.md").read_text(encoding="utf-8")
    assert "canonical modules docs site" in backlog_refinement
    assert "canonical modules docs site" in github_adapter
    assert "planned to migrate to `specfact-cli-modules`" not in backlog_refinement
    assert "planned to migrate to `specfact-cli-modules`" not in github_adapter
