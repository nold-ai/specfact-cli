"""
Code-to-spec sync - Update specs from code changes.

This module provides utilities for syncing code changes to specifications
using AST analysis (CLI can do this without LLM).
"""

from __future__ import annotations

from pathlib import Path

from beartype import beartype
from icontract import ensure, require

from specfact_cli.sync.change_detector import CodeChange


class CodeToSpecSync:
    """Sync code changes to specifications using AST analysis."""

    def __init__(self, repo_path: Path) -> None:
        """
        Initialize code-to-spec sync.

        Args:
            repo_path: Path to repository root
        """
        self.repo_path = repo_path.resolve()

    @beartype
    @require(lambda self, changes: isinstance(changes, list), "Changes must be list")
    @require(lambda self, changes: all(isinstance(c, CodeChange) for c in changes), "All items must be CodeChange")
    @require(lambda self, bundle_name: isinstance(bundle_name, str), "Bundle name must be string")
    @ensure(lambda result: result is None, "Must return None")
    def sync(self, changes: list[CodeChange], bundle_name: str) -> None:
        """
        Sync code changes to specifications using AST analysis.

        Args:
            changes: List of code changes to sync
            bundle_name: Project bundle name
        """
        from specfact_cli.utils.bundle_loader import load_project_bundle, save_project_bundle
        from specfact_cli.utils.structure import SpecFactStructure

        # Load project bundle
        bundle_dir = SpecFactStructure.project_dir(base_path=self.repo_path, bundle_name=bundle_name)
        project_bundle = load_project_bundle(bundle_dir)

        # Group changes by feature
        changes_by_feature: dict[str, list[CodeChange]] = {}
        for change in changes:
            if change.feature_key not in changes_by_feature:
                changes_by_feature[change.feature_key] = []
            changes_by_feature[change.feature_key].append(change)

        # Process each feature
        for feature_key, feature_changes in changes_by_feature.items():
            feature = project_bundle.features.get(feature_key)
            if not feature:
                continue

            # Analyze changed files
            for change in feature_changes:
                file_path = self.repo_path / change.file_path
                if file_path.exists() and feature.source_tracking:
                    # Analyze file and update feature spec
                    # This would use existing CodeAnalyzer to extract function signatures,
                    # contracts, etc., and update the feature accordingly
                    # For now, we'll just update the hash
                    feature.source_tracking.update_hash(file_path)
                    feature.source_tracking.update_sync_timestamp()

        # Save updated project bundle
        save_project_bundle(project_bundle, bundle_dir, atomic=True)
