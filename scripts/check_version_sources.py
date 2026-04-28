#!/usr/bin/env python3
"""Ensure release version strings match across canonical source files."""

from __future__ import annotations

import argparse
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


def _changed_files_vs_git_ref(root: Path, git_ref: str) -> list[str]:
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
        return []
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def _is_packaged_artifact(path_str: str) -> bool:
    """True when staged paths imply a release/version bump must accompany the commit."""
    normalized = path_str.replace("\\", "/")
    if normalized in {"pyproject.toml", "setup.py"}:
        return True
    if normalized.startswith("src/"):
        return True
    # CI-only bundled module snapshot (not part of the distributable version surface).
    if normalized.startswith("resources/bundled-module-registry/"):
        return False
    return normalized.startswith("resources/")


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


def _read_text_for_version_gate(root: Path, relative_posix: str, staged_files: set[str]) -> str:
    """Prefer staged (index) bytes when the path is staged; else working tree."""
    if relative_posix in staged_files:
        staged = _read_staged_blob(root, relative_posix)
        if staged is not None:
            return staged
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


def _version_bumped_vs_git_ref(root: Path, current_version: str, git_ref: str) -> bool:
    """True when the four canonical version strings strictly increase vs ``git_ref`` (semver-aware)."""
    previous_versions: set[str] = set()
    for path in _CANONICAL_VERSION_FILES:
        previous_text = _read_file_at_git_ref(root, git_ref, path)
        if previous_text is None:
            return True
        previous = _version_reader_for(path)(previous_text)
        if previous is None:
            return True
        previous_versions.add(previous)
    if len(previous_versions) != 1:
        return True
    previous_version = previous_versions.pop()
    current_parsed = _parse_semver(current_version)
    previous_parsed = _parse_semver(previous_version)
    if current_parsed is None or previous_parsed is None:
        return current_version != previous_version
    return current_parsed > previous_parsed


def _changelog_has_release_header(changelog_text: str, version: str) -> bool:
    return re.search(rf"(?m)^## \[{re.escape(version)}\] - \d{{4}}-\d{{2}}-\d{{2}}$", changelog_text) is not None


def _enforce_packaged_artifact_versioning(
    root: Path, staged_files: set[str], current_version: str, compare_ref: str
) -> int:
    missing_version_files = [path for path in _CANONICAL_VERSION_FILES if path not in staged_files]
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
    if "CHANGELOG.md" not in staged_files:
        sys.stderr.write(
            "check_version_sources: packaged artifact changes require a staged CHANGELOG.md entry for the new version.\n"
        )
        sys.stderr.write(_REMEDIATION)
        return 1
    changelog_text = _read_text_for_version_gate(root, "CHANGELOG.md", staged_files)
    if _changelog_has_release_header(changelog_text, current_version):
        return 0
    sys.stderr.write(
        "check_version_sources: CHANGELOG.md must contain a release header for the staged package version "
        f"({current_version}).\n"
    )
    sys.stderr.write(_REMEDIATION)
    return 1


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
    changed_vs_ref = ns.changed_vs.strip()
    changed_files = set(_changed_files_vs_git_ref(root, changed_vs_ref)) if changed_vs_ref else set()
    candidate_files = staged_files | changed_files
    paths = {
        "pyproject.toml": root / "pyproject.toml",
        "setup.py": root / "setup.py",
        "src/__init__.py": root / "src" / "__init__.py",
        "src/specfact_cli/__init__.py": root / "src" / "specfact_cli" / "__init__.py",
    }
    versions: dict[str, str] = {}
    for label, path in paths.items():
        if not path.is_file():
            sys.stderr.write(f"check_version_sources: missing file {path.relative_to(root)}\n")
            sys.stderr.write(_REMEDIATION)
            return 2
        text = _read_text_for_version_gate(root, label, staged_files)
        ver = _version_reader_for(label)(text)
        if not ver:
            sys.stderr.write(f"check_version_sources: could not parse version in {label}\n")
            sys.stderr.write(_REMEDIATION)
            return 2
        versions[label] = ver

    unique = sorted(set(versions.values()))
    if len(unique) != 1:
        sys.stderr.write(
            "check_version_sources: version mismatch across pyproject.toml, setup.py, "
            "src/__init__.py, src/specfact_cli/__init__.py:\n"
        )
        for label, ver in sorted(versions.items()):
            sys.stderr.write(f"  {label}: {ver}\n")
        sys.stderr.write(_REMEDIATION)
        return 1

    if any(_is_packaged_artifact(path) for path in candidate_files):
        required_files = changed_files if changed_files else staged_files
        compare_ref = changed_vs_ref if changed_vs_ref else "HEAD"
        return _enforce_packaged_artifact_versioning(root, required_files, unique[0], compare_ref)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
