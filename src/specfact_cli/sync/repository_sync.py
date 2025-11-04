"""
Repository sync implementation.

This module provides synchronization of repository code changes to SpecFact artifacts.
It detects code changes, updates plan artifacts, and tracks deviations from manual plans.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.analyzers.code_analyzer import CodeAnalyzer
from specfact_cli.comparators.plan_comparator import PlanComparator
from specfact_cli.models.plan import PlanBundle
from specfact_cli.validators.schema import validate_plan_bundle


@dataclass
class RepositorySyncResult:
    """
    Result of repository sync operation.

    Attributes:
        status: Sync status ("success" | "deviation_detected" | "error")
        code_changes: List of detected code changes
        plan_updates: List of plan artifact updates
        deviations: List of deviations from manual plan
    """

    status: str
    code_changes: list[dict[str, Any]]
    plan_updates: list[dict[str, Any]]
    deviations: list[dict[str, Any]]

    @beartype
    def __post_init__(self) -> None:
        """Validate RepositorySyncResult after initialization."""
        valid_statuses = ["success", "deviation_detected", "error"]
        if self.status not in valid_statuses:
            msg = f"Status must be one of {valid_statuses}, got {self.status}"
            raise ValueError(msg)


class RepositorySync:
    """
    Sync code changes to SpecFact artifacts.

    Monitors repository code changes, updates plan artifacts based on detected
    features/stories, and tracks deviations from manual plans.
    """

    @beartype
    def __init__(self, repo_path: Path, target: Path | None = None, confidence_threshold: float = 0.5) -> None:
        """
        Initialize repository sync.

        Args:
            repo_path: Path to repository root
            target: Target directory for artifacts (default: .specfact)
            confidence_threshold: Minimum confidence threshold for feature detection
        """
        self.repo_path = Path(repo_path).resolve()
        self.target = Path(target).resolve() if target else self.repo_path / ".specfact"
        self.confidence_threshold = confidence_threshold
        self.hash_store: dict[str, str] = {}
        self.analyzer = CodeAnalyzer(self.repo_path, confidence_threshold)

    @beartype
    @require(lambda repo_path: repo_path.exists(), "Repository path must exist")
    @require(lambda repo_path: repo_path.is_dir(), "Repository path must be a directory")
    @ensure(lambda result: isinstance(result, RepositorySyncResult), "Must return RepositorySyncResult")
    @ensure(lambda result: result.status in ["success", "deviation_detected", "error"], "Status must be valid")
    def sync_repository_changes(self, repo_path: Path | None = None) -> RepositorySyncResult:
        """
        Sync code changes to SpecFact artifacts.

        Args:
            repo_path: Path to repository (default: self.repo_path)

        Returns:
            Repository sync result with code changes, plan updates, and deviations
        """
        if repo_path is None:
            repo_path = self.repo_path

        # 1. Detect code changes
        code_changes = self.detect_code_changes(repo_path)

        # 2. Update plan artifacts based on code changes
        plan_updates = self.update_plan_artifacts(code_changes, self.target)

        # 3. Track deviations from manual plans
        deviations = self.track_deviations(code_changes, self.target)

        # Determine status
        status = "deviation_detected" if deviations else "success"

        return RepositorySyncResult(
            status=status,
            code_changes=code_changes,
            plan_updates=plan_updates,
            deviations=deviations,
        )

    @beartype
    @require(lambda repo_path: repo_path.exists(), "Repository path must exist")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def detect_code_changes(self, repo_path: Path) -> list[dict[str, Any]]:
        """
        Detect code changes in repository.

        Monitors source files in src/ directory and detects modifications
        based on file hashing.

        Args:
            repo_path: Path to repository

        Returns:
            List of detected code changes
        """
        changes: list[dict[str, Any]] = []

        # Monitor source files in src/ directory
        src_dir = repo_path / "src"
        if src_dir.exists():
            for source_file in src_dir.rglob("*.py"):
                if source_file.is_file():
                    relative_path = str(source_file.relative_to(repo_path))
                    current_hash = self._get_file_hash(source_file)
                    stored_hash = self.hash_store.get(relative_path, "")

                    if current_hash != stored_hash:
                        changes.append(
                            {
                                "file": source_file,
                                "hash": current_hash,
                                "type": "modified" if stored_hash else "new",
                                "relative_path": relative_path,
                            }
                        )

        return changes

    @beartype
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def update_plan_artifacts(self, code_changes: list[dict[str, Any]], target: Path) -> list[dict[str, Any]]:
        """
        Update plan artifacts based on code changes.

        Analyzes code changes to extract features/stories and updates
        plan bundle if auto-generated plan exists.

        Args:
            code_changes: List of detected code changes
            target: Target directory for artifacts

        Returns:
            List of plan updates
        """
        updates: list[dict[str, Any]] = []

        if not code_changes:
            return updates

        # Analyze code changes using CodeAnalyzer
        # For now, analyze entire repository if there are changes
        # (could be optimized to only analyze changed files)
        try:
            auto_plan = self.analyzer.analyze()
            if auto_plan and auto_plan.features:
                # Write auto-generated plan to reports directory
                reports_dir = target / "reports" / "repository"
                reports_dir.mkdir(parents=True, exist_ok=True)
                auto_plan_file = reports_dir / "auto-generated-plan.yaml"

                from specfact_cli.generators.plan_generator import PlanGenerator

                generator = PlanGenerator()
                generator.generate(auto_plan, auto_plan_file)

                updates.append(
                    {
                        "plan_file": auto_plan_file,
                        "features": len(auto_plan.features),
                        "stories": sum(len(f.stories) for f in auto_plan.features),
                        "updated": True,
                    }
                )
        except Exception:
            # If analysis fails, continue without update
            pass

        return updates

    @beartype
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def track_deviations(self, code_changes: list[dict[str, Any]], target: Path) -> list[dict[str, Any]]:
        """
        Track deviations from manual plans.

        Compares detected features/stories from code changes against
        manual plan bundle and identifies deviations.

        Args:
            code_changes: List of detected code changes
            target: Target directory for artifacts

        Returns:
            List of deviation dictionaries
        """
        deviations: list[dict[str, Any]] = []

        # Load manual plan
        manual_plan_file = target / "plans" / "main.bundle.yaml"
        if not manual_plan_file.exists():
            return deviations

        # Validate and load manual plan
        is_valid, _error, manual_plan = validate_plan_bundle(manual_plan_file)
        if not is_valid or manual_plan is None:
            return deviations

        # Type guard: manual_plan is not None after check
        assert isinstance(manual_plan, PlanBundle)

        # Generate auto plan from current code
        try:
            auto_plan = self.analyzer.analyze()
            if not auto_plan or not auto_plan.features:
                return deviations

            # Compare manual vs auto plan using PlanComparator
            comparator = PlanComparator()
            comparison = comparator.compare(manual_plan, auto_plan)

            # Convert comparison deviations to sync deviations
            for deviation in comparison.deviations:
                deviations.append(
                    {
                        "type": deviation.type.value if hasattr(deviation.type, "value") else str(deviation.type),
                        "severity": (
                            deviation.severity.value
                            if hasattr(deviation.severity, "value")
                            else str(deviation.severity)
                        ),
                        "description": deviation.description,
                        "location": deviation.location or "",
                        "fix_hint": deviation.suggestion or "",
                    }
                )
        except Exception:
            # If comparison fails, continue without deviations
            pass

        return deviations

    @beartype
    def _get_file_hash(self, file_path: Path) -> str:
        """
        Get file hash for change detection.

        Args:
            file_path: Path to file

        Returns:
            SHA256 hash of file contents
        """
        if not file_path.exists():
            return ""

        with file_path.open("rb") as f:
            content = f.read()
            return hashlib.sha256(content).hexdigest()
