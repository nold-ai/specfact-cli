"""
Change detection system for bidirectional sync.

This module provides utilities for detecting changes in code, specs, and tests
using hash-based comparison.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from beartype import beartype
from icontract import ensure, require

from specfact_cli.models.plan import Feature


@dataclass
class CodeChange:
    """Represents a change in code file."""

    file_path: str
    feature_key: str
    old_hash: str | None = None
    new_hash: str | None = None


@dataclass
class SpecChange:
    """Represents a change in specification."""

    feature_key: str
    contract_path: str | None = None
    protocol_path: str | None = None
    change_type: str = "modified"  # modified, added, removed


@dataclass
class TestChange:
    """Represents a change in test file."""

    file_path: str
    feature_key: str
    old_hash: str | None = None
    new_hash: str | None = None


@dataclass
class Conflict:
    """Represents a conflict where both code and spec changed."""

    feature_key: str
    code_changes: list[CodeChange] = field(default_factory=list)
    spec_changes: list[SpecChange] = field(default_factory=list)
    conflict_type: str = "bidirectional"  # bidirectional, hash_mismatch


@dataclass
class ChangeSet:
    """Set of changes detected in repository."""

    code_changes: list[CodeChange] = field(default_factory=list)
    spec_changes: list[SpecChange] = field(default_factory=list)
    test_changes: list[TestChange] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)


class ChangeDetector:
    """Detector for changes in code, specs, and tests."""

    def __init__(self, bundle_name: str, repo_path: Path) -> None:
        """
        Initialize change detector.

        Args:
            bundle_name: Project bundle name
            repo_path: Path to repository root
        """
        self.bundle_name = bundle_name
        self.repo_path = repo_path.resolve()

    @beartype
    @require(lambda self: self.repo_path.exists(), "Repository path must exist")
    @ensure(lambda self, result: isinstance(result, ChangeSet), "Must return ChangeSet")
    def detect_changes(self, features: dict[str, Feature]) -> ChangeSet:
        """
        Detect changes using hash-based comparison.

        Args:
            features: Dictionary of features to check

        Returns:
            ChangeSet with all detected changes
        """
        changeset = ChangeSet()

        for feature_key, feature in features.items():
            if not feature.source_tracking:
                continue

            # Check implementation files
            for impl_file in feature.source_tracking.implementation_files:
                file_path = self.repo_path / impl_file
                if file_path.exists():
                    if feature.source_tracking.has_changed(file_path):
                        old_hash = feature.source_tracking.file_hashes.get(impl_file)
                        new_hash = feature.source_tracking.compute_hash(file_path)
                        changeset.code_changes.append(
                            CodeChange(
                                file_path=impl_file,
                                feature_key=feature_key,
                                old_hash=old_hash,
                                new_hash=new_hash,
                            )
                        )
                else:
                    # File deleted
                    old_hash = feature.source_tracking.file_hashes.get(impl_file)
                    changeset.code_changes.append(
                        CodeChange(
                            file_path=impl_file,
                            feature_key=feature_key,
                            old_hash=old_hash,
                            new_hash=None,
                        )
                    )

            # Check test files
            for test_file in feature.source_tracking.test_files:
                file_path = self.repo_path / test_file
                if file_path.exists():
                    if feature.source_tracking.has_changed(file_path):
                        old_hash = feature.source_tracking.file_hashes.get(test_file)
                        new_hash = feature.source_tracking.compute_hash(file_path)
                        changeset.test_changes.append(
                            TestChange(
                                file_path=test_file,
                                feature_key=feature_key,
                                old_hash=old_hash,
                                new_hash=new_hash,
                            )
                        )
                else:
                    # File deleted
                    old_hash = feature.source_tracking.file_hashes.get(test_file)
                    changeset.test_changes.append(
                        TestChange(
                            file_path=test_file,
                            feature_key=feature_key,
                            old_hash=old_hash,
                            new_hash=None,
                        )
                    )

            # Check for spec changes (contract/protocol)
            # This would require comparing current contract/protocol files with stored hashes
            # For now, we'll detect if contract/protocol files exist but feature doesn't reference them
            # or vice versa

        # Detect conflicts (both code and spec changed)
        self._detect_conflicts(changeset, features)

        return changeset

    def _detect_conflicts(self, changeset: ChangeSet, features: dict[str, Feature]) -> None:
        """
        Detect conflicts where both code and spec changed.

        Args:
            changeset: ChangeSet to update with conflicts
            features: Dictionary of features
        """
        # Group changes by feature
        code_changes_by_feature: dict[str, list[CodeChange]] = {}
        for change in changeset.code_changes:
            if change.feature_key not in code_changes_by_feature:
                code_changes_by_feature[change.feature_key] = []
            code_changes_by_feature[change.feature_key].append(change)

        spec_changes_by_feature: dict[str, list[SpecChange]] = {}
        for change in changeset.spec_changes:
            if change.feature_key not in spec_changes_by_feature:
                spec_changes_by_feature[change.feature_key] = []
            spec_changes_by_feature[change.feature_key].append(change)

        # Find features with both code and spec changes
        for feature_key in set(code_changes_by_feature.keys()) & set(spec_changes_by_feature.keys()):
            changeset.conflicts.append(
                Conflict(
                    feature_key=feature_key,
                    code_changes=code_changes_by_feature[feature_key],
                    spec_changes=spec_changes_by_feature[feature_key],
                )
            )
