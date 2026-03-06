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


def test_docs_note_module_docs_are_temporarily_hosted_in_core() -> None:
    readme = _repo_file("README.md").read_text(encoding="utf-8")
    docs_index = _repo_file("docs/index.md").read_text(encoding="utf-8")
    assert "temporarily hosted" in readme
    assert "temporarily hosted" in docs_index
