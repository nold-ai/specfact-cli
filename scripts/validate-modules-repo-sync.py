#!/usr/bin/env python3
"""
Validate that specfact-cli-modules repo has the latest module source from the worktree.

Maps each of the 17 migrated modules to its bundle and checks file presence (and optionally content).
Run from specfact-cli worktree root with SPECFACT_MODULES_REPO set to the modules repo path.

--gate: Migration-complete gate (non-reversible). Fails if any file is missing or if any file content
        differs, unless SPECFACT_MIGRATION_CONTENT_VERIFIED=1 (after human verification that
        differences are only import/namespace or that logic has been migrated).

--modified-after: Report which worktree files were last modified (by git) AFTER the corresponding
                  file in the modules repo. Use this to see if any worktree edits were made after
                  the initial migration and never synced to specfact-cli-modules.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

from beartype import beartype
from icontract import ensure


logger = logging.getLogger(__name__)


# Module name -> (bundle package dir, bundle namespace)
MODULE_TO_BUNDLE: dict[str, tuple[str, str]] = {
    "project": ("specfact-project", "specfact_project"),
    "plan": ("specfact-project", "specfact_project"),
    "import_cmd": ("specfact-project", "specfact_project"),
    "sync": ("specfact-project", "specfact_project"),
    "migrate": ("specfact-project", "specfact_project"),
    "backlog": ("specfact-backlog", "specfact_backlog"),
    "policy_engine": ("specfact-backlog", "specfact_backlog"),
    "analyze": ("specfact-codebase", "specfact_codebase"),
    "drift": ("specfact-codebase", "specfact_codebase"),
    "validate": ("specfact-codebase", "specfact_codebase"),
    "repro": ("specfact-codebase", "specfact_codebase"),
    "contract": ("specfact-spec", "specfact_spec"),
    "spec": ("specfact-spec", "specfact_spec"),
    "sdd": ("specfact-spec", "specfact_spec"),
    "generate": ("specfact-spec", "specfact_spec"),
    "enforce": ("specfact-govern", "specfact_govern"),
    "patch_mode": ("specfact-govern", "specfact_govern"),
}


def _git_last_commit_ts(repo_root: Path, rel_path: str) -> int | None:
    """Return last commit timestamp for path in repo, or None if not in git / error."""
    try:
        r = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "--", rel_path],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if r.returncode != 0 or not r.stdout.strip():
            return None
        return int(r.stdout.strip())
    except (ValueError, subprocess.TimeoutExpired):
        return None


def _resolve_modules_root(worktree: Path) -> Path:
    """Resolve modules repo path from env or sibling checkout."""
    modules_repo = os.environ.get("SPECFACT_MODULES_REPO", "")
    if not modules_repo:
        return (worktree.parent.parent / "specfact-cli-modules").resolve()
    return Path(modules_repo).resolve()


def _iter_worktree_files(cli_modules: Path) -> list[tuple[str, Path, Path, bool]]:
    """Collect candidate migrated module files from worktree."""
    files: list[tuple[str, Path, Path, bool]] = []
    for module_name in MODULE_TO_BUNDLE:
        src_dir = cli_modules / module_name / "src"
        if not src_dir.is_dir():
            continue
        inner_dir = src_dir / module_name
        wt_src = inner_dir if inner_dir.is_dir() else src_dir
        use_inner = inner_dir.is_dir()
        for wt_file in wt_src.rglob("*"):
            if wt_file.is_dir():
                continue
            if "__pycache__" in wt_file.parts or wt_file.suffix not in (".py", ".yaml", ".yml", ".json", ".md", ".txt"):
                continue
            files.append((module_name, src_dir, wt_file, use_inner))
    return files


def _collect_presence_data(
    cli_modules: Path,
    packages_root: Path,
) -> tuple[list[tuple[str, Path, Path]], list[tuple[str, Path, Path]], int, int]:
    """Collect matching and missing files across worktree and modules repo."""
    missing: list[tuple[str, Path, Path]] = []
    file_pairs: list[tuple[str, Path, Path]] = []
    present_count = 0
    total_worktree = 0
    for module_name, src_dir, wt_file, use_inner in _iter_worktree_files(cli_modules):
        bundle_dir, bundle_ns = MODULE_TO_BUNDLE[module_name]
        wt_src = src_dir / module_name if use_inner else src_dir
        mod_bundle = packages_root / bundle_dir / "src" / bundle_ns / module_name
        rel = wt_file.relative_to(wt_src)
        mod_file = mod_bundle / module_name / rel if use_inner else mod_bundle / rel
        total_worktree += 1
        if mod_file.exists():
            present_count += 1
            file_pairs.append((module_name, wt_file, mod_file))
        else:
            missing.append((module_name, wt_file, mod_file))
    return missing, file_pairs, present_count, total_worktree


def _collect_only_in_modules(cli_modules: Path, packages_root: Path) -> list[Path]:
    """Collect files that exist only in modules repo."""
    only_in_modules: list[Path] = []
    for bundle_dir in packages_root.iterdir():
        if not bundle_dir.is_dir():
            continue
        src_dir = bundle_dir / "src"
        if not src_dir.is_dir():
            continue
        for ns_dir in src_dir.iterdir():
            if not ns_dir.is_dir():
                continue
            for module_name, (bundle_dir_name, bundle_ns) in MODULE_TO_BUNDLE.items():
                if bundle_dir.name != bundle_dir_name or ns_dir.name != bundle_ns:
                    continue
                mod_module = ns_dir / module_name
                if not mod_module.is_dir():
                    continue
                only_in_modules.extend(_collect_module_only_files(cli_modules, module_name, mod_module))
                break
    return only_in_modules


def _collect_module_only_files(cli_modules: Path, module_name: str, mod_module: Path) -> list[Path]:
    """Collect files present in the modules repo but missing from the matching worktree module."""
    module_only_files: list[Path] = []
    inner_dir = cli_modules / module_name / "src" / module_name
    use_inner = inner_dir.is_dir()
    default_src = cli_modules / module_name / "src"
    for mod_file in mod_module.rglob("*"):
        if mod_file.is_dir() or "__pycache__" in mod_file.parts:
            continue
        rel = mod_file.relative_to(mod_module)
        if use_inner and len(rel.parts) > 1 and rel.parts[0] == module_name:
            wt_rel = rel.relative_to(Path(rel.parts[0]))
            wt_src = inner_dir
        else:
            wt_rel = rel
            wt_src = default_src
        if wt_src.is_dir() and not (wt_src / wt_rel).exists():
            module_only_files.append(mod_file)
    return module_only_files


def _report_modified_after(
    worktree: Path,
    modules_root: Path,
    file_pairs: list[tuple[str, Path, Path]],
) -> int:
    """Report files changed in worktree after modules repo counterpart."""
    logger.info("=== Modified-after check (worktree vs modules repo by last git commit) ===")
    logger.info("Worktree:     %s", worktree)
    logger.info("Modules repo: %s", modules_root)
    worktree_newer: list[tuple[str, Path, Path, int, int]] = []
    modules_newer_or_same: list[tuple[str, Path, Path, int, int]] = []
    unknown: list[tuple[str, Path, Path]] = []
    for module_name, wt_file, mod_file in file_pairs:
        wt_rel = wt_file.relative_to(worktree)
        mod_rel = mod_file.relative_to(modules_root)
        ts_w = _git_last_commit_ts(worktree, str(wt_rel))
        ts_m = _git_last_commit_ts(modules_root, str(mod_rel))
        if ts_w is None or ts_m is None:
            unknown.append((module_name, wt_file, mod_file))
            continue
        if ts_w > ts_m:
            worktree_newer.append((module_name, wt_file, mod_file, ts_w, ts_m))
        else:
            modules_newer_or_same.append((module_name, wt_file, mod_file, ts_w, ts_m))
    logger.info("Total file pairs:        %d", len(file_pairs))
    logger.info(
        "Worktree modified AFTER: %d (worktree has newer commits - not synced to modules repo)", len(worktree_newer)
    )
    logger.info("Modules newer or same:   %d", len(modules_newer_or_same))
    logger.info("Unknown (no git history): %d", len(unknown))
    if worktree_newer:
        logger.info("--- Files last modified in WORKTREE after modules repo (candidate to sync) ---")
        for mod_name, wt_path, _mod_path, ts_w, ts_m in sorted(worktree_newer, key=lambda x: (x[0], str(x[1]))):
            logger.info("  %s: %s  (wt_ts=%d > mod_ts=%d)", mod_name, wt_path.relative_to(worktree), ts_w, ts_m)
        logger.warning("Result: Worktree has edits after migration; sync these to specfact-cli-modules if needed.")
        return 1
    if unknown:
        logger.info("--- Files with unknown git history (not in git or error) ---")
        for mod_name, wt_path, _mod_path in sorted(unknown, key=lambda x: (x[0], str(x[1])))[:20]:
            logger.info("  %s: %s", mod_name, wt_path.relative_to(worktree))
        if len(unknown) > 20:
            logger.info("  ... and %d more", len(unknown) - 20)
    logger.info("Result: No worktree file was last modified after its counterpart in modules repo.")
    return 0


def _resolve_branch_name(modules_root: Path) -> str:
    """Resolve the current branch name for the modules repo."""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=modules_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception:
        return "?"
    return result.stdout.strip() if result.returncode == 0 else "?"


def _collect_content_diffs(
    cli_modules: Path,
    packages_root: Path,
) -> tuple[list[tuple[str, Path, Path]], int]:
    """Collect Python content mismatches between worktree and modules repo."""
    import hashlib

    content_diffs: list[tuple[str, Path, Path]] = []
    total_py = 0
    for module_name, (bundle_dir, bundle_ns) in MODULE_TO_BUNDLE.items():
        src_dir = cli_modules / module_name / "src"
        if not src_dir.is_dir():
            continue
        inner_dir = src_dir / module_name
        wt_src = inner_dir if inner_dir.is_dir() else src_dir
        use_inner = inner_dir.is_dir()
        mod_bundle = packages_root / bundle_dir / "src" / bundle_ns / module_name
        for wt_file in wt_src.rglob("*.py"):
            if wt_file.is_dir() or "__pycache__" in wt_file.parts:
                continue
            rel = wt_file.relative_to(wt_src)
            mod_file = (mod_bundle / module_name / rel) if use_inner else (mod_bundle / rel)
            if not mod_file.exists():
                continue
            total_py += 1
            if hashlib.sha256(wt_file.read_bytes()).hexdigest() != hashlib.sha256(mod_file.read_bytes()).hexdigest():
                content_diffs.append((module_name, wt_file, mod_file))
    return content_diffs, total_py


def _report_content_diffs(
    gate: bool,
    content_diffs: list[tuple[str, Path, Path]],
    total_py: int,
    worktree: Path,
    modules_root: Path,
) -> int:
    """Report content mismatches and return the appropriate exit code."""
    if not content_diffs:
        return 0
    if gate:
        logger.info("--- CONTENT DIFFERS (migration gate) ---")
        for mod_name, wt_path, mod_path in sorted(content_diffs, key=lambda x: (x[0], str(x[1]))):
            logger.info("  %s: %s vs %s", mod_name, wt_path.relative_to(worktree), mod_path.relative_to(modules_root))
        if len(content_diffs) > 20:
            logger.info("  ... and %d more", len(content_diffs) - 20)
        if os.environ.get("SPECFACT_MIGRATION_CONTENT_VERIFIED") == "1":
            logger.info(
                "SPECFACT_MIGRATION_CONTENT_VERIFIED=1 set: %d content diffs accepted (expected: worktree=shim-era, repo=migrated bundle). Gate passes.",
                len(content_diffs),
            )
            return 0
        logger.error(
            "Migration gate: content differs. Ensure all logic is in specfact-cli-modules, then re-run with"
            "  SPECFACT_MIGRATION_CONTENT_VERIFIED=1 to pass (non-reversible gate)."
        )
        return 1
    logger.info(
        "Content: %d identical, %d differ (import/namespace changes in repo are expected).",
        total_py - len(content_diffs),
        len(content_diffs),
    )
    return 0


@beartype
@ensure(lambda result: result >= 0, "exit code must be non-negative")
def main() -> int:
    gate = "--gate" in sys.argv
    modified_after = "--modified-after" in sys.argv
    worktree = Path(__file__).resolve().parent.parent
    modules_root = _resolve_modules_root(worktree)
    if not modules_root.is_dir():
        logger.error("Modules repo not found: %s", modules_root)
        return 1

    cli_modules = worktree / "src" / "specfact_cli" / "modules"
    if not cli_modules.is_dir():
        logger.error("Worktree modules not found: %s", cli_modules)
        return 1

    packages_root = modules_root / "packages"
    if not packages_root.is_dir():
        logger.error("packages/ not found in modules repo: %s", packages_root)
        return 1

    missing, file_pairs, present_count, total_worktree = _collect_presence_data(cli_modules, packages_root)
    only_in_modules = _collect_only_in_modules(cli_modules, packages_root)

    logger.info("=== specfact-cli-modules validation vs worktree ===")
    logger.info("Worktree:     %s", worktree)
    logger.info("Modules repo: %s", modules_root)
    branch = _resolve_branch_name(modules_root)
    logger.info("Branch:       %s", branch)
    logger.info("Worktree files (migrated modules): %d", total_worktree)
    logger.info("Present in modules repo:          %d", present_count)
    logger.info("Missing in modules repo:          %d", len(missing))
    logger.info("Only in modules repo:             %d", len(only_in_modules))

    if missing:
        logger.info("--- MISSING in specfact-cli-modules (in worktree but not in repo) ---")
        for mod_name, wt_path, mod_path in sorted(missing, key=lambda x: (x[0], str(x[1]))):
            logger.info("  %s: %s -> %s", mod_name, wt_path.relative_to(worktree), mod_path.relative_to(modules_root))

    if only_in_modules:
        logger.info("--- ONLY in specfact-cli-modules (not in worktree under same module) ---")
        for p in sorted(only_in_modules)[:30]:
            logger.info("  %s", p.relative_to(modules_root))
        if len(only_in_modules) > 30:
            logger.info("  ... and %d more", len(only_in_modules) - 30)

    if missing:
        logger.error("Result: FAIL - some worktree files are missing in modules repo.")
        return 1
    if total_worktree == 0:
        logger.info("Result: SKIP - no migrated module source found under worktree src/specfact_cli/modules/*/src/")
        return 0

    if modified_after:
        return _report_modified_after(worktree, modules_root, file_pairs)

    content_diffs, total_py = _collect_content_diffs(cli_modules, packages_root)
    content_diff_exit_code = _report_content_diffs(gate, content_diffs, total_py, worktree, modules_root)
    if content_diff_exit_code != 0:
        return content_diff_exit_code

    logger.info("Result: OK - all worktree module files are present in modules repo.")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    sys.exit(main())
