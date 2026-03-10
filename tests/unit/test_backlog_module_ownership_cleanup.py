from __future__ import annotations

from pathlib import Path

from specfact_cli.registry import module_packages
from specfact_cli.utils.ide_setup import SPECFACT_COMMANDS


REPO_ROOT = Path(__file__).resolve().parents[2]


def _contains_shipped_backlog_module_content(path: Path) -> bool:
    """Return True when a backlog-core path still contains source/manifests, not generated residue."""
    if not path.exists():
        return False
    if path.is_file():
        return True
    ignored_dirs = {"__pycache__", "logs", ".pytest_cache"}
    ignored_suffixes = {".pyc", ".pyo"}
    for child in path.rglob("*"):
        if any(part in ignored_dirs for part in child.parts):
            continue
        if child.is_dir():
            continue
        if child.suffix in ignored_suffixes:
            continue
        return True
    return False


def test_core_repo_no_longer_ships_backlog_owned_command_surfaces() -> None:
    """Core should not retain backlog-owned command packages or shims after migration."""
    forbidden_paths = [
        REPO_ROOT / "modules" / "backlog-core",
        REPO_ROOT / "src" / "specfact_cli" / "commands" / "backlog_commands.py",
        REPO_ROOT / "src" / "specfact_cli" / "groups" / "backlog_group.py",
    ]

    existing = [
        str(path.relative_to(REPO_ROOT)) for path in forbidden_paths if _contains_shipped_backlog_module_content(path)
    ]
    assert not existing, f"Core still ships backlog-owned command surfaces: {existing}"


def test_core_prompt_export_surface_excludes_backlog_prompts_and_templates() -> None:
    """Backlog prompts/templates must no longer ship from core resources."""
    forbidden_paths = [
        REPO_ROOT / "resources" / "prompts" / "specfact.backlog-add.md",
        REPO_ROOT / "resources" / "prompts" / "specfact.backlog-daily.md",
        REPO_ROOT / "resources" / "prompts" / "specfact.backlog-refine.md",
        REPO_ROOT / "resources" / "prompts" / "specfact.sync-backlog.md",
        REPO_ROOT / "resources" / "templates" / "backlog",
    ]

    existing = [str(path.relative_to(REPO_ROOT)) for path in forbidden_paths if path.exists()]
    assert not existing, f"Core still exports backlog prompt/template assets: {existing}"

    forbidden_prompt_ids = {
        "specfact.backlog-add",
        "specfact.backlog-daily",
        "specfact.backlog-refine",
        "specfact.sync-backlog",
    }
    leaked_prompt_ids = sorted(forbidden_prompt_ids.intersection(SPECFACT_COMMANDS))
    assert not leaked_prompt_ids, f"Core IDE prompt list still includes backlog prompt ids: {leaked_prompt_ids}"


def test_backlog_duplicate_overlap_tolerance_is_not_required() -> None:
    """Registry merge logic should not special-case split backlog ownership anymore."""
    duplicate_tolerance = getattr(module_packages, "_is_expected_duplicate_extension", None)
    if duplicate_tolerance is None:
        return

    tolerated = [
        pair
        for pair in [
            ("backlog", "daily"),
            ("backlog", "refine"),
            ("backlog", "init-config"),
            ("backlog", "map-fields"),
            ("backlog auth", "github"),
        ]
        if duplicate_tolerance("nold-ai/specfact-backlog", pair[0], pair[1])
    ]
    assert not tolerated, f"Backlog duplicate overlap is still specially tolerated: {tolerated}"
