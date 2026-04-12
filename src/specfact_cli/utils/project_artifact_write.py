"""Safe writes into user-owned project artifacts (init/setup trust boundary)."""

from __future__ import annotations

import json
import re
import shutil
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Final, cast

from beartype import beartype
from icontract import ensure, require

from specfact_cli.common import get_bridge_logger


_logger = get_bridge_logger(__name__)

RECOVERY_SUBDIR: Final[str] = ".specfact/recovery"


class ProjectArtifactWriteError(RuntimeError):
    """Blocked or unsafe write into a user project artifact."""


class StructuredJsonDocumentError(ProjectArtifactWriteError):
    """JSON settings cannot be merged without data loss or repair."""


class ProjectWriteMode(StrEnum):
    """Declared write semantics for a project artifact (policy surface)."""

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


@beartype
@require(lambda repo_root: repo_root.exists() and repo_root.is_dir())
@require(lambda source: source.is_file())
@ensure(lambda result: result.is_file())
def backup_file_to_recovery(repo_root: Path, source: Path) -> Path:
    """Copy ``source`` into ``.specfact/recovery`` with a UTC timestamp suffix."""
    recovery_dir = (repo_root / RECOVERY_SUBDIR).resolve()
    recovery_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", source.name)
    dest = recovery_dir / f"{safe_name}.{stamp}.bak"
    shutil.copy2(source, dest)
    return dest


@beartype
@require(lambda repo_path: repo_path.exists() and repo_path.is_dir())
@require(lambda settings_relative: settings_relative.strip() != "")
@require(lambda prompt_files: all(isinstance(p, str) for p in prompt_files))
@ensure(lambda result: result.exists() and result.is_file())
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

    Preserves all other top-level keys and non-SpecFact recommendation paths. On invalid JSON or
    unusable ``chat`` / ``promptFilesRecommendations`` shape, raises ``StructuredJsonDocumentError``
    unless ``explicit_replace_unparseable`` is True (backup, then recoverable rewrite).
    """
    settings_path = (repo_path / settings_relative).resolve()
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path: Path | None = None

    if not settings_path.exists():
        payload: dict[str, Any] = {"chat": {"promptFilesRecommendations": list(prompt_files)}}
        settings_path.write_text(json.dumps(payload, indent=4) + "\n", encoding="utf-8")
        return settings_path

    raw_text = settings_path.read_text(encoding="utf-8")
    loaded: Any
    try:
        loaded = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        if not explicit_replace_unparseable:
            raise StructuredJsonDocumentError(
                f"Cannot merge into {settings_path}: invalid JSON ({exc.msg} at line {exc.lineno} col {exc.colno}). "
                "Fix the file or re-run with --force to replace it after a backup under .specfact/recovery/."
            ) from exc
        backup_path = backup_file_to_recovery(repo_path, settings_path)
        _logger.info("Backed up unparseable settings to %s", backup_path)
        loaded = {}

    if not isinstance(loaded, dict):
        if not explicit_replace_unparseable:
            raise StructuredJsonDocumentError(
                f"Cannot merge into {settings_path}: root value must be a JSON object, not {type(loaded).__name__}."
            )
        if backup_path is None:
            backup_path = backup_file_to_recovery(repo_path, settings_path)
            _logger.info("Backed up settings before replace to %s", backup_path)
        loaded = {}

    chat_block = loaded.get("chat", {})
    if not isinstance(chat_block, dict):
        if not explicit_replace_unparseable:
            raise StructuredJsonDocumentError(
                f'Cannot merge into {settings_path}: "chat" must be a JSON object, not {type(chat_block).__name__}.'
            )
        if backup_path is None:
            backup_path = backup_file_to_recovery(repo_path, settings_path)
            _logger.info("Backed up settings before chat coercion to %s", backup_path)
        chat_block = {}
        loaded["chat"] = chat_block

    existing_recommendations = chat_block.get("promptFilesRecommendations", [])
    if not isinstance(existing_recommendations, list):
        if not explicit_replace_unparseable:
            raise StructuredJsonDocumentError(
                f'Cannot merge into {settings_path}: "chat.promptFilesRecommendations" must be a JSON array.'
            )
        if backup_path is None:
            backup_path = backup_file_to_recovery(repo_path, settings_path)
            _logger.info("Backed up settings before recommendations coercion to %s", backup_path)
        existing_recommendations = []

    recs_as_strings = [str(x) for x in existing_recommendations]
    if strip_specfact_github_from_existing:
        recs_as_strings = _strip_specfact_github_prompt_recommendations(recs_as_strings)

    merged_list = _ordered_unique_strings([*recs_as_strings, *prompt_files])
    chat_block = cast(dict[str, Any], chat_block)
    chat_block["promptFilesRecommendations"] = merged_list
    loaded["chat"] = chat_block

    settings_path.write_text(json.dumps(loaded, indent=4) + "\n", encoding="utf-8")
    return settings_path
