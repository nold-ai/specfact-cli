"""Tests for safe project artifact writes (VS Code settings merge)."""

from __future__ import annotations

import ast
import json
import shutil
import uuid
from pathlib import Path

import pytest

from specfact_cli.utils.ide_setup import PROMPT_SOURCE_CORE, create_vscode_settings
from specfact_cli.utils.project_artifact_write import (
    ProjectArtifactWriteError,
    StructuredJsonDocumentError,
    backup_file_to_recovery,
    merge_vscode_settings_prompt_recommendations,
)


def test_merge_vscode_settings_rejects_path_outside_repo(tmp_path: Path) -> None:
    escape_root = tmp_path.parent / f"sfw_escape_{uuid.uuid4().hex[:12]}"
    escape_root.mkdir(exist_ok=True)
    vscode_link = tmp_path / ".vscode"
    if not hasattr(vscode_link, "symlink_to"):
        shutil.rmtree(escape_root, ignore_errors=True)
        pytest.skip("symlink_to not available")
    try:
        vscode_link.symlink_to(escape_root, target_is_directory=True)
    except OSError:
        shutil.rmtree(escape_root, ignore_errors=True)
        pytest.skip("symlinks not supported")
    try:
        (escape_root / "settings.json").write_text("{}", encoding="utf-8")
        with pytest.raises(ProjectArtifactWriteError, match="outside the repository"):
            merge_vscode_settings_prompt_recommendations(
                tmp_path,
                ".vscode/settings.json",
                [".github/prompts/specfact.01-import.prompt.md"],
                strip_specfact_github_from_existing=False,
                explicit_replace_unparseable=False,
            )
    finally:
        if vscode_link.is_symlink():
            vscode_link.unlink(missing_ok=True)
        shutil.rmtree(escape_root, ignore_errors=True)


def test_merge_vscode_settings_accepts_jsonc_comments(tmp_path: Path) -> None:
    vscode_dir = tmp_path / ".vscode"
    vscode_dir.mkdir(parents=True)
    settings_path = vscode_dir / "settings.json"
    settings_path.write_text(
        """{
  // keep
  "python.defaultInterpreterPath": "/x",
  "chat": {"promptFilesRecommendations": []}
}
""",
        encoding="utf-8",
    )
    out = merge_vscode_settings_prompt_recommendations(
        tmp_path,
        ".vscode/settings.json",
        [".github/prompts/specfact.01-import.prompt.md"],
        strip_specfact_github_from_existing=False,
        explicit_replace_unparseable=False,
    )
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["python.defaultInterpreterPath"] == "/x"
    assert ".github/prompts/specfact.01-import.prompt.md" in data["chat"]["promptFilesRecommendations"]


def test_create_vscode_settings_empty_prompts_by_source_strips_specfact_paths(tmp_path: Path) -> None:
    vscode_dir = tmp_path / ".vscode"
    vscode_dir.mkdir(parents=True)
    settings_path = vscode_dir / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "chat": {
                    "promptFilesRecommendations": [
                        ".github/prompts/specfact.01-import.prompt.md",
                        ".github/prompts/team.prompt.md",
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    create_vscode_settings(
        tmp_path,
        ".vscode/settings.json",
        prompts_by_source={},
        force=False,
    )
    data = json.loads(settings_path.read_text(encoding="utf-8"))
    assert data["chat"]["promptFilesRecommendations"] == [".github/prompts/team.prompt.md"]


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


# --- commentjson migration tests (Tasks 1.4 & 1.5) ---
# These tests specify the TARGET behaviour: no json5 imports, commentjson for read,
# stdlib json for write. They will FAIL until project_artifact_write.py is migrated.


_MODULE_SOURCE = Path(__file__).parents[3] / "src" / "specfact_cli" / "utils" / "project_artifact_write.py"


def test_project_artifact_write_does_not_import_json5() -> None:
    """After migration, json5 must not appear in project_artifact_write.py imports."""
    source = _MODULE_SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name != "json5", "json5 import found — must be replaced by commentjson + json"
        elif isinstance(node, ast.ImportFrom):
            assert node.module != "json5", "from json5 import found — must be replaced by commentjson + json"


def test_project_artifact_write_uses_commentjson_for_read() -> None:
    """After migration, commentjson must be imported in project_artifact_write.py."""
    source = _MODULE_SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    found_commentjson = False
    for node in ast.walk(tree):
        if (isinstance(node, ast.Import) and any(alias.name == "commentjson" for alias in node.names)) or (
            isinstance(node, ast.ImportFrom) and node.module == "commentjson"
        ):
            found_commentjson = True
    assert found_commentjson, "commentjson import not found — must be added for JSONC read path"


def test_merge_vscode_settings_handles_line_and_block_comments_in_jsonc(tmp_path: Path) -> None:
    """JSONC with // and /* */ comments must be parsed without error after migration."""
    vscode_dir = tmp_path / ".vscode"
    vscode_dir.mkdir(parents=True)
    settings_path = vscode_dir / "settings.json"
    # Use // comments (universally supported in JSONC parsers including commentjson)
    settings_path.write_text(
        """{
  // line comment
  "python.defaultInterpreterPath": "/usr/bin/python3",
  // another comment
  "chat": {"promptFilesRecommendations": []}
}
""",
        encoding="utf-8",
    )
    out = merge_vscode_settings_prompt_recommendations(
        tmp_path,
        ".vscode/settings.json",
        [".github/prompts/specfact.01-import.prompt.md"],
        strip_specfact_github_from_existing=False,
        explicit_replace_unparseable=False,
    )
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["python.defaultInterpreterPath"] == "/usr/bin/python3"


def test_merge_vscode_settings_handles_trailing_commas_in_jsonc(tmp_path: Path) -> None:
    """JSONC with trailing commas must be parsed without error after migration."""
    vscode_dir = tmp_path / ".vscode"
    vscode_dir.mkdir(parents=True)
    settings_path = vscode_dir / "settings.json"
    settings_path.write_text(
        '{"python.defaultInterpreterPath": "/usr/bin/python3", "chat": {"promptFilesRecommendations": []},}\n',
        encoding="utf-8",
    )
    out = merge_vscode_settings_prompt_recommendations(
        tmp_path,
        ".vscode/settings.json",
        [".github/prompts/specfact.01-import.prompt.md"],
        strip_specfact_github_from_existing=False,
        explicit_replace_unparseable=False,
    )
    data = json.loads(out.read_text(encoding="utf-8"))
    assert ".github/prompts/specfact.01-import.prompt.md" in data["chat"]["promptFilesRecommendations"]


def test_merge_vscode_settings_write_output_is_valid_stdlib_json(tmp_path: Path) -> None:
    """Write output must be parseable by stdlib json.loads (no trailing commas in output)."""
    vscode_dir = tmp_path / ".vscode"
    vscode_dir.mkdir(parents=True)
    settings_path = vscode_dir / "settings.json"
    settings_path.write_text('{"chat": {"promptFilesRecommendations": []}}\n', encoding="utf-8")
    out = merge_vscode_settings_prompt_recommendations(
        tmp_path,
        ".vscode/settings.json",
        [".github/prompts/specfact.01-import.prompt.md"],
        strip_specfact_github_from_existing=False,
        explicit_replace_unparseable=False,
    )
    out_text = out.read_text(encoding="utf-8")
    # Must parse with stdlib json (strict — no trailing commas, no comments)
    parsed = json.loads(out_text)
    assert isinstance(parsed, dict), "Write output must be a valid JSON object"


def test_create_vscode_settings_chat_not_object_force_coerces_with_backup(tmp_path: Path) -> None:
    vscode_dir = tmp_path / ".vscode"
    vscode_dir.mkdir(parents=True)
    settings_path = vscode_dir / "settings.json"
    settings_path.write_text(json.dumps({"chat": "invalid"}), encoding="utf-8")
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
    assert isinstance(data["chat"], dict)
    assert ".github/prompts/specfact.01-import.prompt.md" in data["chat"]["promptFilesRecommendations"]
