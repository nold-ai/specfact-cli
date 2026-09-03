#!/usr/bin/env python3
"""Ensure release version strings match across canonical source files."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

from beartype import beartype
from icontract import ensure


_REMEDIATION = """\
REMEDIATION (same check as .github/workflows/pr-orchestrator.yml → tests job):
  1. Set the SAME semver string in all four places:
       - pyproject.toml → project.version
       - setup.py → version=
       - src/__init__.py → __version__
       - src/specfact_cli/__init__.py → __version__
  2. Validate: hatch run check-version-sources
  3. If you bumped the CLI for release: add a top CHANGELOG.md section like  ## [x.y.z] - YYYY-MM-DD
  4. If publishing: local version must be strictly greater than PyPI; run with network:
       SPECFACT_PYPI_VERSION_CHECK_LENIENT_NETWORK=1 python scripts/check_local_version_ahead_of_pypi.py
     (offline: SPECFACT_SKIP_PYPI_VERSION_CHECK=1 — do not use in CI.)
"""

_CANONICAL_VERSION_FILES = (
    "pyproject.toml",
    "setup.py",
    "src/__init__.py",
    "src/specfact_cli/__init__.py",
)
_VERSION_PATTERNS = {
    "pyproject.toml": r'(?m)^version\s*=\s*["\']([^"\']+)["\']',
    "setup.py": r'version\s*=\s*["\']([^"\']+)["\']',
    "src/__init__.py": r'(?m)^__version__\s*=\s*["\']([^"\']+)["\']',
    "src/specfact_cli/__init__.py": r'(?m)^__version__\s*=\s*["\']([^"\']+)["\']',
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read_version_with_pattern(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text)
    return match.group(1) if match else None


def _staged_files(root: Path) -> list[str]:
    try:
        completed = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMRD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        sys.stderr.write(f"check_version_sources: cannot list staged files ({exc})\n")
        return []
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def _changed_files_vs_git_ref(root: Path, git_ref: str) -> list[str] | None:
    try:
        completed = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACMRD", f"{git_ref}...HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        sys.stderr.write(f"check_version_sources: cannot list changed files vs {git_ref} ({exc})\n")
        return None
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def _default_changed_vs_ref(root: Path) -> str:
    """Use the fetched PR target so follow-up commits share one release bundle."""
    target_branch = os.environ.get("GITHUB_BASE_REF", "").strip()
    if not target_branch:
        try:
            completed = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            return ""
        target_branch = "main" if completed.stdout.strip() == "main" else "dev"
    candidate = f"refs/remotes/origin/{target_branch}"
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", f"{candidate}^{{commit}}"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return ""
    return candidate if completed.returncode == 0 else ""


def _selected_changed_vs_ref(root: Path, explicit_ref: str, staged_files: set[str]) -> str:
    """Prefer an explicit CI base, otherwise discover a local staged-change base."""
    if explicit_ref or not staged_files:
        return explicit_ref
    return _default_changed_vs_ref(root)


def _is_packaged_artifact(path_str: str) -> bool:
    """True when staged paths imply a release/version bump must accompany the commit."""
    normalized = path_str.replace("\\", "/")
    if normalized == "setup.py":
        return True
    if normalized.startswith("src/"):
        return True
    # CI-only bundled module snapshot (not part of the distributable version surface).
    if normalized.startswith("resources/bundled-module-registry/"):
        return False
    return normalized.startswith("resources/")


def _candidate_requires_versioning(
    root: Path,
    candidate_files: set[str],
    compare_ref: str,
    current_version: str,
) -> bool:
    """Return whether changed files imply a package version/changelog bundle."""
    for path in candidate_files:
        normalized = path.replace("\\", "/")
        if normalized == "pyproject.toml":
            if _version_bumped_vs_git_ref(root, current_version, compare_ref):
                return True
            continue
        if _is_packaged_artifact(normalized):
            return True
    return False


def _parse_semver(version: str) -> tuple[int, int, int] | None:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", version.strip())
    if match is None:
        return None
    major, minor, patch = match.groups()
    return (int(major), int(minor), int(patch))


def _read_staged_blob(root: Path, relative_posix: str) -> str | None:
    """Return index (staged) content for ``relative_posix``, or None if unavailable."""
    try:
        completed = subprocess.run(
            ["git", "show", f":{relative_posix}"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return completed.stdout


def _read_text_for_version_gate(
    root: Path,
    relative_posix: str,
    staged_files: set[str],
    *,
    committed_fallback: bool,
) -> str:
    """Read the would-be commit: staged bytes first, then HEAD when requested."""
    if relative_posix in staged_files:
        staged = _read_staged_blob(root, relative_posix)
        return staged if staged is not None else ""
    if committed_fallback:
        committed = _read_file_at_git_ref(root, "HEAD", relative_posix)
        return committed if committed is not None else ""
    path = root / relative_posix
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _read_file_at_git_ref(root: Path, git_ref: str, relative_path: str) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "show", f"{git_ref}:{relative_path}"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return completed.stdout


def _version_reader_for(label: str):
    return lambda text: _read_version_with_pattern(text, _VERSION_PATTERNS[label])


def _canonical_version_at_git_ref(root: Path, git_ref: str) -> str | None:
    """Return one synchronized canonical version from ``git_ref``, failing closed."""
    versions: set[str] = set()
    for path in _CANONICAL_VERSION_FILES:
        text = _read_file_at_git_ref(root, git_ref, path)
        if text is None:
            return None
        version = _version_reader_for(path)(text)
        if version is None:
            return None
        versions.add(version)
    return versions.pop() if len(versions) == 1 else None


def _version_bumped_vs_git_ref(root: Path, current_version: str, git_ref: str) -> bool:
    """True when the four canonical version strings strictly increase vs ``git_ref`` (semver-aware)."""
    previous_version = _canonical_version_at_git_ref(root, git_ref)
    if previous_version is None:
        return False
    current_parsed = _parse_semver(current_version)
    previous_parsed = _parse_semver(previous_version)
    if current_parsed is None or previous_parsed is None:
        return False
    return current_parsed > previous_parsed


def _changelog_has_release_header(changelog_text: str, version: str) -> bool:
    return re.search(rf"(?m)^## \[{re.escape(version)}\] - \d{{4}}-\d{{2}}-\d{{2}}$", changelog_text) is not None


def _enforce_packaged_artifact_versioning(
    root: Path,
    required_files: set[str],
    staged_files: set[str],
    current_version: str,
    compare_ref: str,
) -> int:
    missing_version_files = [path for path in _CANONICAL_VERSION_FILES if path not in required_files]
    if missing_version_files:
        sys.stderr.write(
            "check_version_sources: packaged artifact changes require staging all four canonical version files:\n"
        )
        for path in missing_version_files:
            sys.stderr.write(f"  missing staged version file: {path}\n")
        sys.stderr.write(_REMEDIATION)
        return 1
    if not _version_bumped_vs_git_ref(root, current_version, compare_ref):
        sys.stderr.write(
            "check_version_sources: packaged artifact changes require incrementing the package version "
            "across all four canonical version files.\n"
        )
        sys.stderr.write(_REMEDIATION)
        return 1
    if "CHANGELOG.md" not in required_files:
        sys.stderr.write(
            "check_version_sources: packaged artifact changes require a staged CHANGELOG.md entry for the new version.\n"
        )
        sys.stderr.write(_REMEDIATION)
        return 1
    changelog_text = _read_text_for_version_gate(
        root,
        "CHANGELOG.md",
        staged_files,
        committed_fallback=True,
    )
    if _changelog_has_release_header(changelog_text, current_version):
        return 0
    sys.stderr.write(
        "check_version_sources: CHANGELOG.md must contain a release header for the staged package version "
        f"({current_version}).\n"
    )
    sys.stderr.write(_REMEDIATION)
    return 1


def _read_candidate_versions(
    root: Path,
    staged_files: set[str],
    *,
    committed_fallback: bool,
) -> dict[str, str] | None:
    """Parse canonical versions from the would-be commit snapshot."""
    versions: dict[str, str] = {}
    for label in _CANONICAL_VERSION_FILES:
        path = root / label
        if not path.is_file():
            sys.stderr.write(f"check_version_sources: missing file {label}\n")
            sys.stderr.write(_REMEDIATION)
            return None
        text = _read_text_for_version_gate(
            root,
            label,
            staged_files,
            committed_fallback=committed_fallback,
        )
        version = _version_reader_for(label)(text)
        if version is None:
            sys.stderr.write(f"check_version_sources: could not parse version in {label}\n")
            sys.stderr.write(_REMEDIATION)
            return None
        versions[label] = version
    return versions


def _report_version_mismatch(versions: dict[str, str]) -> None:
    sys.stderr.write(
        "check_version_sources: version mismatch across pyproject.toml, setup.py, "
        "src/__init__.py, src/specfact_cli/__init__.py:\n"
    )
    for label, version in sorted(versions.items()):
        sys.stderr.write(f"  {label}: {version}\n")
    sys.stderr.write(_REMEDIATION)


@beartype
@ensure(lambda result: result >= 0, "exit code must be non-negative")
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check canonical version source consistency.")
    parser.add_argument(
        "--changed-vs",
        metavar="GIT_REV",
        default="",
        help=(
            "Treat files changed since GIT_REV...HEAD as the candidate release surface. "
            "Used by CI on clean checkouts where the index is empty."
        ),
    )
    ns = parser.parse_args([] if argv is None else argv)
    root = _repo_root()
    staged_files = set(_staged_files(root))
    changed_vs_ref = _selected_changed_vs_ref(root, ns.changed_vs.strip(), staged_files)
    changed_result = _changed_files_vs_git_ref(root, changed_vs_ref) if changed_vs_ref else []
    if changed_result is None:
        return 2
    changed_files = set(changed_result)
    candidate_files = staged_files | changed_files
    committed_fallback = bool(staged_files or changed_vs_ref)
    versions = _read_candidate_versions(root, staged_files, committed_fallback=committed_fallback)
    if versions is None:
        return 2

    unique = sorted(set(versions.values()))
    if len(unique) != 1:
        _report_version_mismatch(versions)
        return 1

    reuses_branch_release = bool(changed_vs_ref and unique[0] == _canonical_version_at_git_ref(root, "HEAD"))
    compare_ref = changed_vs_ref if reuses_branch_release else "HEAD"
    if _candidate_requires_versioning(root, candidate_files, compare_ref, unique[0]):
        required_files = changed_files if reuses_branch_release else staged_files
        return _enforce_packaged_artifact_versioning(
            root,
            required_files,
            staged_files,
            unique[0],
            compare_ref,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
