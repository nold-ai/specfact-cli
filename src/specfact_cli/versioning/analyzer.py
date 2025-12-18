"""Change analysis and version bump recommendation for project bundles."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

from beartype import beartype
from git import Repo
from git.exc import InvalidGitRepositoryError, NoSuchPathError
from icontract import ensure, require

from specfact_cli.models.project import ProjectBundle
from specfact_cli.utils.bundle_loader import load_project_bundle


class ChangeType(str, Enum):
    """Change categories mapped to SemVer bumps."""

    NONE = "none"
    PATCH = "patch"
    ADDITIVE = "additive"
    BREAKING = "breaking"


@dataclass
class VersionAnalysis:
    """Result of bundle change analysis."""

    change_type: ChangeType
    recommended_bump: str
    changed_files: list[str]
    reasons: list[str]
    content_hash: str | None = None


SEMVER_PATTERN = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+].*)?$")


@beartype
def validate_semver(version: str) -> tuple[int, int, int]:
    """
    Validate SemVer string and return numeric parts.

    Args:
        version: Version string (e.g., "1.2.3")

    Returns:
        Tuple of (major, minor, patch)

    Raises:
        ValueError: If version is not valid SemVer
    """
    match = SEMVER_PATTERN.match(version)
    if not match:
        raise ValueError(f"Invalid SemVer version: {version}")

    major, minor, patch = match.groups()
    return int(major), int(minor), int(patch)


@beartype
@require(lambda bump_type: bump_type in {"major", "minor", "patch"}, "bump_type must be major|minor|patch")
@ensure(lambda result: isinstance(result, str), "Must return version string")
def bump_version(version: str, bump_type: str) -> str:
    """
    Bump SemVer string according to bump_type.

    Args:
        version: Current version (SemVer)
        bump_type: One of major|minor|patch

    Returns:
        New version string
    """
    major, minor, patch = validate_semver(version)

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    else:
        patch += 1

    return f"{major}.{minor}.{patch}"


class ChangeAnalyzer:
    """Analyze bundle changes to recommend version bumps."""

    @beartype
    def __init__(self, repo_path: Path | str = ".") -> None:
        self.repo_path = Path(repo_path)

    @staticmethod
    def _map_change_to_bump(change_type: ChangeType) -> str:
        if change_type == ChangeType.BREAKING:
            return "major"
        if change_type == ChangeType.ADDITIVE:
            return "minor"
        if change_type == ChangeType.PATCH:
            return "patch"
        return "none"

    @beartype
    def _load_repo(self) -> Repo | None:
        try:
            return Repo(self.repo_path, search_parent_directories=True)
        except (InvalidGitRepositoryError, NoSuchPathError):
            return None

    @staticmethod
    def _diff_paths(diff_entries: Iterable, bundle_dir: Path, workdir: Path) -> list[tuple[str, str]]:
        """Return (status, path) tuples filtered to bundle_dir."""
        bundle_dir = bundle_dir.resolve()
        filtered: list[tuple[str, str]] = []
        for entry in diff_entries:
            # prefer b_path when present (handles renames/edits), fallback to a_path
            raw_path = entry.b_path or entry.a_path
            if not raw_path:
                continue
            abs_path = workdir.joinpath(raw_path).resolve()
            if bundle_dir in abs_path.parents or abs_path == bundle_dir:
                filtered.append((entry.change_type.upper(), raw_path))
        return filtered

    @staticmethod
    def _collect_untracked(repo: Repo, bundle_dir: Path) -> list[str]:
        bundle_dir = bundle_dir.resolve()
        working_dir = Path(repo.working_tree_dir or ".").resolve()
        untracked: list[str] = []
        for path_str in repo.untracked_files:
            abs_path = working_dir.joinpath(path_str).resolve()
            if bundle_dir in abs_path.parents or abs_path == bundle_dir:
                untracked.append(path_str)
        return untracked

    @beartype
    def analyze(self, bundle_dir: Path, bundle: ProjectBundle | None = None) -> VersionAnalysis:
        """
        Analyze bundle changes and recommend a version bump.

        Args:
            bundle_dir: Path to project bundle directory
            bundle: Optional pre-loaded ProjectBundle (avoids re-loading)

        Returns:
            VersionAnalysis with change_type and recommendation
        """
        repo = self._load_repo()
        changed_files: list[str] = []
        reasons: list[str] = []
        change_type = ChangeType.NONE

        if repo:
            workdir = Path(repo.working_tree_dir or ".").resolve()
            # Staged, unstaged, and untracked changes scoped to the bundle
            staged = self._diff_paths(repo.index.diff("HEAD"), bundle_dir, workdir)
            unstaged = self._diff_paths(repo.index.diff(None), bundle_dir, workdir)
            untracked = self._collect_untracked(repo, bundle_dir)

            changed_files = [path for _, path in staged + unstaged] + untracked

            has_breaking = any(status == "D" for status, _ in staged + unstaged)
            has_additive = any(status == "A" for status, _ in staged + unstaged) or bool(untracked)
            has_modified = any(status == "M" for status, _ in staged + unstaged)

            if has_breaking:
                change_type = ChangeType.BREAKING
                reasons.append("Detected deletions in bundle files (breaking).")
            elif has_additive:
                change_type = ChangeType.ADDITIVE
                reasons.append("Detected new bundle files (additive).")
            elif has_modified:
                change_type = ChangeType.PATCH
                reasons.append("Detected modified bundle files (patch).")
            else:
                reasons.append("No Git changes detected for bundle.")
        else:
            reasons.append("Git repository not found; falling back to hash comparison.")

        content_hash: str | None = None
        try:
            bundle_obj = bundle or load_project_bundle(bundle_dir, validate_hashes=False, progress_callback=None)
            summary = bundle_obj.compute_summary(include_hash=True)
            content_hash = summary.content_hash
            baseline_hash = bundle_obj.manifest.bundle.get("content_hash")

            if change_type == ChangeType.NONE:
                if baseline_hash and content_hash and baseline_hash != content_hash:
                    change_type = ChangeType.PATCH
                    reasons.append("Bundle content hash changed since last recorded hash.")
                elif not baseline_hash:
                    reasons.append("No baseline content hash recorded; recommend setting via version bump or set.")
        except Exception as exc:  # pragma: no cover - defensive logging
            reasons.append(f"Skipped bundle hash analysis: {exc}")

        recommended_bump = self._map_change_to_bump(change_type)

        return VersionAnalysis(
            change_type=change_type,
            recommended_bump=recommended_bump,
            changed_files=changed_files,
            reasons=reasons,
            content_hash=content_hash,
        )

    @staticmethod
    @beartype
    @ensure(lambda result: isinstance(result, dict), "Must return history entry dict")
    def create_history_entry(old_version: str, new_version: str, change_type: str) -> dict[str, str]:
        """
        Create structured history entry for manifest.project_metadata.

        Args:
            old_version: Previous version
            new_version: New version
            change_type: Bump type (major|minor|patch|set)

        Returns:
            Dictionary suitable for ProjectMetadata.version_history append
        """
        return {
            "from": old_version,
            "to": new_version,
            "change_type": change_type,
            "changed_at": datetime.now(UTC).isoformat(),
        }
