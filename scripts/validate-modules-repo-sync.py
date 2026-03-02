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

import os
import subprocess
import sys
from pathlib import Path


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


def main() -> int:
    gate = "--gate" in sys.argv
    modified_after = "--modified-after" in sys.argv
    worktree = Path(__file__).resolve().parent.parent
    modules_repo = os.environ.get("SPECFACT_MODULES_REPO", "")
    if not modules_repo:
        modules_repo = worktree.parent.parent / "specfact-cli-modules"
    modules_root = Path(modules_repo).resolve()
    if not modules_root.is_dir():
        print(f"Modules repo not found: {modules_root}", file=sys.stderr)
        return 1

    cli_modules = worktree / "src" / "specfact_cli" / "modules"
    if not cli_modules.is_dir():
        print(f"Worktree modules not found: {cli_modules}", file=sys.stderr)
        return 1

    packages_root = modules_root / "packages"
    if not packages_root.is_dir():
        print(f"packages/ not found in modules repo: {packages_root}", file=sys.stderr)
        return 1

    missing: list[tuple[str, Path, Path]] = []
    only_in_modules: list[Path] = []
    file_pairs: list[tuple[str, Path, Path]] = []  # (module_name, wt_file, mod_file) for existing pairs
    present_count = 0
    total_worktree = 0

    for module_name, (bundle_dir, bundle_ns) in MODULE_TO_BUNDLE.items():
        src_dir = cli_modules / module_name / "src"
        if not src_dir.is_dir():
            continue
        # Flat: module/src/{__init__.py, app.py, commands.py, ...}; Nested: module/src/module_name/{...}
        inner_dir = src_dir / module_name
        if inner_dir.is_dir():
            wt_src = inner_dir
            use_inner = True  # repo has .../module_name/module_name/...
        else:
            wt_src = src_dir
            use_inner = False
        mod_bundle = packages_root / bundle_dir / "src" / bundle_ns / module_name
        for wt_file in wt_src.rglob("*"):
            if wt_file.is_dir():
                continue
            if "__pycache__" in wt_file.parts or wt_file.suffix not in (".py", ".yaml", ".yml", ".json", ".md", ".txt"):
                continue
            total_worktree += 1
            rel = wt_file.relative_to(wt_src)
            mod_file = mod_bundle / module_name / rel if use_inner else mod_bundle / rel
            if mod_file.exists():
                present_count += 1
                file_pairs.append((module_name, wt_file, mod_file))
            else:
                missing.append((module_name, wt_file, mod_file))

    for bundle_dir in packages_root.iterdir():
        if not bundle_dir.is_dir():
            continue
        src_dir = bundle_dir / "src"
        if not src_dir.is_dir():
            continue
        for ns_dir in src_dir.iterdir():
            if not ns_dir.is_dir():
                continue
            for module_name in MODULE_TO_BUNDLE:
                bundle_dir_name, bundle_ns = MODULE_TO_BUNDLE[module_name]
                if bundle_dir.name != bundle_dir_name or ns_dir.name != bundle_ns:
                    continue
                mod_module = ns_dir / module_name
                if not mod_module.is_dir():
                    continue
                inner_dir = cli_modules / module_name / "src" / module_name
                use_inner = inner_dir.is_dir()
                for mod_file in mod_module.rglob("*"):
                    if mod_file.is_dir():
                        continue
                    if "__pycache__" in mod_file.parts:
                        continue
                    rel = mod_file.relative_to(mod_module)
                    if use_inner and len(rel.parts) > 1 and rel.parts[0] == module_name:
                        wt_rel = rel.relative_to(Path(rel.parts[0]))
                        wt_src = inner_dir
                    else:
                        wt_rel = rel
                        wt_src = cli_modules / module_name / "src"
                    if not wt_src.is_dir():
                        continue
                    wt_file = wt_src / wt_rel
                    if not wt_file.exists():
                        only_in_modules.append(mod_file)
                break

    print("=== specfact-cli-modules validation vs worktree ===\n")
    print(f"Worktree:     {worktree}")
    print(f"Modules repo: {modules_root}")
    print("Branch:       ", end="")
    try:
        r = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=modules_root,
            capture_output=True,
            text=True,
            check=False,
        )
        print(r.stdout.strip() if r.returncode == 0 else "?")
    except Exception:
        print("?")
    print()
    print(f"Worktree files (migrated modules): {total_worktree}")
    print(f"Present in modules repo:          {present_count}")
    print(f"Missing in modules repo:          {len(missing)}")
    print(f"Only in modules repo:             {len(only_in_modules)}")
    print()

    if missing:
        print("--- MISSING in specfact-cli-modules (in worktree but not in repo) ---")
        for mod_name, wt_path, mod_path in sorted(missing, key=lambda x: (x[0], str(x[1]))):
            print(f"  {mod_name}: {wt_path.relative_to(worktree)} -> {mod_path.relative_to(modules_root)}")
        print()

    if only_in_modules:
        print("--- ONLY in specfact-cli-modules (not in worktree under same module) ---")
        for p in sorted(only_in_modules)[:30]:
            print(f"  {p.relative_to(modules_root)}")
        if len(only_in_modules) > 30:
            print(f"  ... and {len(only_in_modules) - 30} more")
        print()

    if missing:
        print("Result: FAIL - some worktree files are missing in modules repo.")
        return 1
    if total_worktree == 0:
        print("Result: SKIP - no migrated module source found under worktree src/specfact_cli/modules/*/src/")
        return 0

    if modified_after:
        # Report which worktree files were last modified (by git) after the corresponding file in modules repo.
        print("=== Modified-after check (worktree vs modules repo by last git commit) ===\n")
        print(f"Worktree:     {worktree}")
        print(f"Modules repo: {modules_root}\n")
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
        print(f"Total file pairs:        {len(file_pairs)}")
        print(
            f"Worktree modified AFTER: {len(worktree_newer)} (worktree has newer commits — not synced to modules repo)"
        )
        print(f"Modules newer or same:   {len(modules_newer_or_same)}")
        print(f"Unknown (no git history): {len(unknown)}")
        print()
        if worktree_newer:
            print("--- Files last modified in WORKTREE after modules repo (candidate to sync) ---")
            for mod_name, wt_path, _mod_path, ts_w, ts_m in sorted(worktree_newer, key=lambda x: (x[0], str(x[1]))):
                print(f"  {mod_name}: {wt_path.relative_to(worktree)}  (wt_ts={ts_w} > mod_ts={ts_m})")
            print()
            print("Result: Worktree has edits after migration; sync these to specfact-cli-modules if needed.")
            return 1
        if unknown:
            print("--- Files with unknown git history (not in git or error) ---")
            for mod_name, wt_path, _mod_path in sorted(unknown, key=lambda x: (x[0], str(x[1])))[:20]:
                print(f"  {mod_name}: {wt_path.relative_to(worktree)}")
            if len(unknown) > 20:
                print(f"  ... and {len(unknown) - 20} more")
            print()
        print("Result: No worktree file was last modified after its counterpart in modules repo.")
        return 0

    # Content comparison (full if --gate, else spot-check)
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

    if content_diffs:
        if gate:
            print("--- CONTENT DIFFERS (migration gate) ---")
            for mod_name, wt_path, mod_path in sorted(content_diffs, key=lambda x: (x[0], str(x[1]))):
                print(f"  {mod_name}: {wt_path.relative_to(worktree)} vs {mod_path.relative_to(modules_root)}")
            if len(content_diffs) > 20:
                print(f"  ... and {len(content_diffs) - 20} more")
            print()
            if os.environ.get("SPECFACT_MIGRATION_CONTENT_VERIFIED") == "1":
                print(
                    f"SPECFACT_MIGRATION_CONTENT_VERIFIED=1 set: {len(content_diffs)} content diffs accepted (expected: worktree=shim-era, repo=migrated bundle). Gate passes."
                )
            else:
                print(
                    "Migration gate: content differs. Ensure all logic is in specfact-cli-modules, then re-run with\n"
                    "  SPECFACT_MIGRATION_CONTENT_VERIFIED=1 to pass (non-reversible gate)."
                )
                return 1
        else:
            print(
                f"Content: {total_py - len(content_diffs)} identical, {len(content_diffs)} differ (import/namespace changes in repo are expected)."
            )

    print("Result: OK - all worktree module files are present in modules repo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
