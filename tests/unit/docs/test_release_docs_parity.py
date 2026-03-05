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
