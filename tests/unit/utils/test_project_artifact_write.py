"""Tests for safe project artifact writes (VS Code settings merge)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from specfact_cli.utils.ide_setup import PROMPT_SOURCE_CORE, create_vscode_settings
from specfact_cli.utils.project_artifact_write import (
    StructuredJsonDocumentError,
    backup_file_to_recovery,
    merge_vscode_settings_prompt_recommendations,
)


def test_merge_vscode_settings_creates_file_when_missing(tmp_path: Path) -> None:
    """New repo: write only managed recommendations."""
    out = merge_vscode_settings_prompt_recommendations(
        tmp_path,
        ".vscode/settings.json",
        [".github/prompts/specfact.01-import.prompt.md"],
        strip_specfact_github_from_existing=False,
        explicit_replace_unparseable=False,
    )
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["chat"]["promptFilesRecommendations"] == [".github/prompts/specfact.01-import.prompt.md"]


def test_backup_file_to_recovery_writes_under_specfact(tmp_path: Path) -> None:
    src = tmp_path / "sample.json"
    src.write_text('{"a": 1}', encoding="utf-8")
    dest = backup_file_to_recovery(tmp_path, src)
    assert dest.is_file()
    assert ".specfact/recovery" in str(dest.relative_to(tmp_path))
    assert dest.read_text(encoding="utf-8") == '{"a": 1}'


def test_create_vscode_settings_malformed_json_raises_and_leaves_file(tmp_path: Path) -> None:
    vscode_dir = tmp_path / ".vscode"
    vscode_dir.mkdir(parents=True)
    settings_path = vscode_dir / "settings.json"
    garbage = "{ not json ,\n"
    settings_path.write_text(garbage, encoding="utf-8")
    prompt = tmp_path / "specfact.01-import.md"
    prompt.write_text("---\n---\n", encoding="utf-8")
    with pytest.raises(StructuredJsonDocumentError):
        create_vscode_settings(
            tmp_path,
            ".vscode/settings.json",
            prompts_by_source={PROMPT_SOURCE_CORE: [prompt]},
            force=False,
        )
    assert settings_path.read_text(encoding="utf-8") == garbage


def test_create_vscode_settings_preserves_unrelated_keys(tmp_path: Path) -> None:
    vscode_dir = tmp_path / ".vscode"
    vscode_dir.mkdir(parents=True)
    settings_path = vscode_dir / "settings.json"
    original = {
        "python.defaultInterpreterPath": "/usr/bin/python3",
        "chat": {"otherSetting": True, "promptFilesRecommendations": []},
    }
    settings_path.write_text(json.dumps(original), encoding="utf-8")
    prompt = tmp_path / "specfact.01-import.md"
    prompt.write_text("---\n---\n", encoding="utf-8")
    create_vscode_settings(
        tmp_path,
        ".vscode/settings.json",
        prompts_by_source={PROMPT_SOURCE_CORE: [prompt]},
        force=False,
    )
    data = json.loads(settings_path.read_text(encoding="utf-8"))
    assert data["python.defaultInterpreterPath"] == "/usr/bin/python3"
    assert data["chat"]["otherSetting"] is True
    assert ".github/prompts/specfact.01-import.prompt.md" in data["chat"]["promptFilesRecommendations"]


def test_create_vscode_settings_force_replaces_unparseable_with_backup(tmp_path: Path) -> None:
    vscode_dir = tmp_path / ".vscode"
    vscode_dir.mkdir(parents=True)
    settings_path = vscode_dir / "settings.json"
    settings_path.write_text("{broken", encoding="utf-8")
    prompt = tmp_path / "specfact.01-import.md"
    prompt.write_text("---\n---\n", encoding="utf-8")
    create_vscode_settings(
        tmp_path,
        ".vscode/settings.json",
        prompts_by_source={PROMPT_SOURCE_CORE: [prompt]},
        force=True,
    )
    recovery = tmp_path / ".specfact" / "recovery"
    assert recovery.is_dir()
    assert any(recovery.glob("settings.json.*.bak"))
    data = json.loads(settings_path.read_text(encoding="utf-8"))
    assert ".github/prompts/specfact.01-import.prompt.md" in data["chat"]["promptFilesRecommendations"]


def test_create_vscode_settings_chat_not_object_raises_without_force(tmp_path: Path) -> None:
    vscode_dir = tmp_path / ".vscode"
    vscode_dir.mkdir(parents=True)
    settings_path = vscode_dir / "settings.json"
    settings_path.write_text(json.dumps({"chat": "invalid"}), encoding="utf-8")
    prompt = tmp_path / "specfact.01-import.md"
    prompt.write_text("---\n---\n", encoding="utf-8")
    with pytest.raises(StructuredJsonDocumentError):
        create_vscode_settings(
            tmp_path,
            ".vscode/settings.json",
            prompts_by_source={PROMPT_SOURCE_CORE: [prompt]},
            force=False,
        )
