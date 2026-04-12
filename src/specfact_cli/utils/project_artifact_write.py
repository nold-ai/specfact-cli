"""Safe writes into user-owned project artifacts (init/setup trust boundary)."""

from __future__ import annotations

import re
import shutil
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Final, cast

import json5
from beartype import beartype
from icontract import ensure, require

from specfact_cli.common import get_bridge_logger
from specfact_cli.utils.contract_predicates import (
    file_path_is_file,
    prompt_files_all_strings,
    repo_path_exists,
    repo_path_is_dir,
    settings_relative_nonblank,
)


_logger = get_bridge_logger(__name__)

RECOVERY_SUBDIR: Final[str] = ".specfact/recovery"


class ProjectArtifactWriteError(RuntimeError):
    """Blocked or unsafe write into a user project artifact."""


class StructuredJsonDocumentError(ProjectArtifactWriteError):
    """JSON settings cannot be merged without data loss or repair."""


class ProjectWriteMode(StrEnum):
    """Declared write semantics for a project artifact (policy surface).

    Reserved for future write-dispatch routing (CREATE_ONLY, MERGE_STRUCTURED, EXPLICIT_REPLACE). Not yet wired into
    call sites; kept so policy enums stay aligned with the OpenSpec safe-artifact-write narrative without churning
    public module layout later.
    """

    CREATE_ONLY = "create_only"
    MERGE_STRUCTURED = "merge_structured"
    EXPLICIT_REPLACE = "explicit_replace"


@beartype
def _is_specfact_github_prompt_path(path: str) -> bool:
    """True for SpecFact-managed GitHub prompt recommendations (strip on selective export)."""
    normalized = path.replace("\\", "/").lstrip("./")
    if not normalized.startswith("github/prompts/"):
        return False
    name = Path(normalized).name
    return bool(name.startswith("specfact") and name.endswith(".prompt.md"))


@beartype
def _strip_specfact_github_prompt_recommendations(paths: list[str]) -> list[str]:
    """Remove prior SpecFact-managed ``.github/prompts/`` entries; keep team-owned paths."""
    return [p for p in paths if not _is_specfact_github_prompt_path(p)]


@beartype
def _ordered_unique_strings(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _write_new_vscode_settings_file(settings_path: Path, prompt_files: list[str]) -> None:
    payload: dict[str, Any] = {"chat": {"promptFilesRecommendations": list(prompt_files)}}
    text = json5.dumps(payload, indent=4, quote_keys=True, trailing_commas=False) + "\n"
    settings_path.write_text(text, encoding="utf-8")


def _ensure_backup(
    repo_path: Path,
    settings_path: Path,
    backup_path: Path | None,
) -> Path:
    if backup_path is not None:
        return backup_path
    return backup_file_to_recovery(repo_path, settings_path)


def _load_root_dict_from_settings_text(
    settings_path: Path,
    repo_path: Path,
    raw_text: str,
    explicit_replace_unparseable: bool,
    backup_path: Path | None,
) -> tuple[dict[str, Any], Path | None]:
    out_backup = backup_path
    try:
        loaded = json5.loads(raw_text)
    except ValueError as exc:
        if not explicit_replace_unparseable:
            raise StructuredJsonDocumentError(
                f"Cannot merge into {settings_path}: invalid JSON/JSONC ({exc}). "
                "Fix the file or re-run with --force to replace it after a backup under .specfact/recovery/."
            ) from exc
        out_backup = _ensure_backup(repo_path, settings_path, out_backup)
        _logger.info("Backed up unparseable settings to %s", out_backup)
        return {}, out_backup

    if isinstance(loaded, dict):
        return loaded, out_backup

    if not explicit_replace_unparseable:
        raise StructuredJsonDocumentError(
            f"Cannot merge into {settings_path}: root value must be a JSON object, not {type(loaded).__name__}."
        )
    out_backup = _ensure_backup(repo_path, settings_path, out_backup)
    _logger.info("Backed up settings before replace to %s", out_backup)
    return {}, out_backup


def _merge_chat_and_recommendations(
    loaded: dict[str, Any],
    settings_path: Path,
    repo_path: Path,
    explicit_replace_unparseable: bool,
    backup_path: Path | None,
    strip_specfact_github_from_existing: bool,
    prompt_files: list[str],
) -> None:
    out_backup = backup_path
    if "chat" not in loaded:
        loaded["chat"] = {}
    chat_block = loaded["chat"]
    if not isinstance(chat_block, dict):
        if not explicit_replace_unparseable:
            raise StructuredJsonDocumentError(
                f'Cannot merge into {settings_path}: "chat" must be a JSON object, not {type(chat_block).__name__}.'
            )
        out_backup = _ensure_backup(repo_path, settings_path, out_backup)
        _logger.info("Backed up settings before chat coercion to %s", out_backup)
        chat_block = {}
        loaded["chat"] = chat_block

    existing_recommendations = chat_block.get("promptFilesRecommendations", [])
    if not isinstance(existing_recommendations, list):
        if not explicit_replace_unparseable:
            raise StructuredJsonDocumentError(
                f'Cannot merge into {settings_path}: "chat.promptFilesRecommendations" must be a JSON array.'
            )
        out_backup = _ensure_backup(repo_path, settings_path, out_backup)
        _logger.info("Backed up settings before recommendations coercion to %s", out_backup)
        existing_recommendations = []

    recs_as_strings = [str(x) for x in existing_recommendations]
    if strip_specfact_github_from_existing:
        recs_as_strings = _strip_specfact_github_prompt_recommendations(recs_as_strings)

    merged_list = _ordered_unique_strings([*recs_as_strings, *prompt_files])
    chat_typed = cast(dict[str, Any], chat_block)
    chat_typed["promptFilesRecommendations"] = merged_list
    loaded["chat"] = chat_typed


@beartype
@require(repo_path_exists, "Repo path must exist")
@require(repo_path_is_dir, "Repo path must be a directory")
@require(file_path_is_file, "file_path must be an existing file")
@ensure(lambda result: isinstance(result, Path) and result.is_file())
def backup_file_to_recovery(repo_path: Path, file_path: Path) -> Path:
    """Copy ``file_path`` into ``.specfact/recovery`` with a UTC timestamp suffix."""
    recovery_dir = (repo_path / RECOVERY_SUBDIR).resolve()
    recovery_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", file_path.name)
    dest = recovery_dir / f"{safe_name}.{stamp}.bak"
    suffix = 0
    while dest.exists():
        suffix += 1
        dest = recovery_dir / f"{safe_name}.{stamp}.{suffix}.bak"
    shutil.copy2(file_path, dest)
    return dest


@beartype
@require(repo_path_exists, "Repo path must exist")
@require(repo_path_is_dir, "Repo path must be a directory")
@require(settings_relative_nonblank, "settings_relative must be non-empty")
@require(prompt_files_all_strings, "prompt_files must be a list of str")
@ensure(lambda result: isinstance(result, Path) and result.exists() and result.is_file())
def merge_vscode_settings_prompt_recommendations(
    repo_path: Path,
    settings_relative: str,
    prompt_files: list[str],
    *,
    strip_specfact_github_from_existing: bool,
    explicit_replace_unparseable: bool,
) -> Path:
    """
    Merge SpecFact ``chat.promptFilesRecommendations`` into VS Code ``settings.json``.

    Preserves all other top-level keys and non-SpecFact recommendation paths. On invalid JSON/JSONC or
    unusable ``chat`` / ``promptFilesRecommendations`` shape, raises ``StructuredJsonDocumentError``
    unless ``explicit_replace_unparseable`` is True (backup, then recoverable rewrite).

    Parses with JSON5 (comments and trailing commas). Serialized output is canonical JSON5/JSON without
    preserving original comment text or formatting from the input file.
    """
    repo_root = repo_path.resolve()
    settings_path = (repo_path / settings_relative).resolve()
    try:
        settings_path.relative_to(repo_root)
    except ValueError as exc:
        raise ProjectArtifactWriteError(
            f"Refusing to write VS Code settings outside the repository: {settings_path}"
        ) from exc

    settings_path.parent.mkdir(parents=True, exist_ok=True)

    if not settings_path.exists():
        _write_new_vscode_settings_file(settings_path, prompt_files)
        return settings_path

    raw_text = settings_path.read_text(encoding="utf-8")
    loaded, backup_path = _load_root_dict_from_settings_text(
        settings_path,
        repo_path,
        raw_text,
        explicit_replace_unparseable,
        None,
    )
    _merge_chat_and_recommendations(
        loaded,
        settings_path,
        repo_path,
        explicit_replace_unparseable,
        backup_path,
        strip_specfact_github_from_existing,
        prompt_files,
    )
    out_text = json5.dumps(loaded, indent=4, quote_keys=True, trailing_commas=False) + "\n"
    settings_path.write_text(out_text, encoding="utf-8")
    return settings_path
