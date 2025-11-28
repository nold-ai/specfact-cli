"""
Drift detection system for identifying misalignment between code and specs.

This module provides utilities for detecting drift between actual code/tests
and specifications, including orphaned code, missing specs, and contract violations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require


@dataclass
class DriftReport:
    """Comprehensive drift analysis report."""

    added_code: list[str] = field(default_factory=list)  # Files with no spec
    removed_code: list[str] = field(default_factory=list)  # Deleted but spec exists
    modified_code: list[str] = field(default_factory=list)  # Hash changed
    orphaned_specs: list[str] = field(default_factory=list)  # Spec with no code
    test_coverage_gaps: list[tuple[str, str]] = field(default_factory=list)  # (feature_key, story_key) missing tests
    contract_violations: list[str] = field(default_factory=list)  # Implementation doesn't match contract


class DriftDetector:
    """Detector for drift between code and specifications."""

    def __init__(self, bundle_name: str, repo_path: Path) -> None:
        """
        Initialize drift detector.

        Args:
            bundle_name: Project bundle name
            repo_path: Path to repository root
        """
        self.bundle_name = bundle_name
        self.repo_path = repo_path.resolve()

    @beartype
    @require(lambda self: self.repo_path.exists(), "Repository path must exist")
    @require(lambda self, bundle_name: isinstance(bundle_name, str), "Bundle name must be string")
    @ensure(lambda self, bundle_name, result: isinstance(result, DriftReport), "Must return DriftReport")
    def scan(self, bundle_name: str, repo_path: Path) -> DriftReport:
        """
        Comprehensive drift analysis.

        Args:
            bundle_name: Project bundle name
            repo_path: Path to repository

        Returns:
            DriftReport with all detected drift issues
        """
        from specfact_cli.utils.bundle_loader import load_project_bundle
        from specfact_cli.utils.structure import SpecFactStructure

        report = DriftReport()

        # Load project bundle
        bundle_dir = SpecFactStructure.project_dir(base_path=repo_path, bundle_name=bundle_name)
        if not bundle_dir.exists():
            return report

        project_bundle = load_project_bundle(bundle_dir)

        # Track all files referenced in specs
        spec_tracked_files: set[str] = set()

        # Check each feature
        for feature_key, feature in project_bundle.features.items():
            if feature.source_tracking:
                # Check implementation files
                for impl_file in feature.source_tracking.implementation_files:
                    spec_tracked_files.add(impl_file)
                    file_path = repo_path / impl_file

                    if not file_path.exists():
                        # File deleted but spec exists
                        report.removed_code.append(impl_file)
                    elif feature.source_tracking.has_changed(file_path):
                        # File modified
                        report.modified_code.append(impl_file)

                # Check test files
                for test_file in feature.source_tracking.test_files:
                    spec_tracked_files.add(test_file)
                    file_path = repo_path / test_file

                    if not file_path.exists():
                        report.removed_code.append(test_file)
                    elif feature.source_tracking.has_changed(file_path):
                        report.modified_code.append(test_file)

                # Check test coverage gaps
                for story in feature.stories:
                    if not story.test_functions:
                        report.test_coverage_gaps.append((feature_key, story.key))

            else:
                # Feature has no source tracking - orphaned spec
                report.orphaned_specs.append(feature_key)

        # Scan repository for untracked code files
        for pattern in ["src/**/*.py", "lib/**/*.py", "app/**/*.py"]:
            for file_path in repo_path.glob(pattern):
                rel_path = str(file_path.relative_to(repo_path))
                # Skip test files and common non-implementation files
                if (
                    "test" in rel_path.lower()
                    or "__pycache__" in rel_path
                    or ".specfact" in rel_path
                    or rel_path in spec_tracked_files
                ):
                    continue
                # Check if it's a Python file that should be tracked
                if file_path.suffix == ".py" and self._is_implementation_file(file_path):
                    report.added_code.append(rel_path)

        # Validate contracts with Specmatic (if available)
        self._detect_contract_violations(project_bundle, bundle_dir, report)

        return report

    def _is_implementation_file(self, file_path: Path) -> bool:
        """Check if file is an implementation file."""
        # Exclude test files
        if "test" in file_path.name.lower() or file_path.name.startswith("test_"):
            return False
        # Exclude common non-implementation directories
        excluded_dirs = {"__pycache__", ".git", ".venv", "venv", "node_modules", ".specfact", "tests", "test"}
        return not any(part in excluded_dirs for part in file_path.parts)

    def _detect_contract_violations(self, project_bundle: Any, bundle_dir: Path, report: DriftReport) -> None:
        """Detect contract violations using Specmatic."""
        from specfact_cli.integrations.specmatic import check_specmatic_available

        is_available, _ = check_specmatic_available()
        if not is_available:
            return  # Skip if Specmatic not available

        # Check each feature with a contract
        for _feature_key, feature in project_bundle.features.items():
            if feature.contract:
                contract_path = bundle_dir / feature.contract
                if contract_path.exists():
                    # In a full implementation, we would:
                    # 1. Start the actual API server
                    # 2. Run Specmatic contract tests
                    # 3. Detect violations
                    # For now, we'll just note that contract validation should be run
                    # This would be done via `specfact spec test` command
                    pass
