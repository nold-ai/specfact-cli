"""
Bridge-based bidirectional sync implementation.

This module provides adapter-agnostic bidirectional synchronization between
external tool artifacts and SpecFact project bundles using bridge configuration.
The sync layer reads bridge config, resolves paths dynamically, and delegates
to adapter-specific parsers/generators.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.models.bridge import AdapterType, BridgeConfig
from specfact_cli.models.project import ProjectBundle
from specfact_cli.sync.bridge_probe import BridgeProbe
from specfact_cli.utils.bundle_loader import load_project_bundle, save_project_bundle


@dataclass
class SyncOperation:
    """Represents a sync operation (import or export)."""

    artifact_key: str  # Artifact key (e.g., "specification", "plan")
    feature_id: str  # Feature identifier (e.g., "001-auth")
    direction: str  # "import" or "export"
    bundle_name: str  # Project bundle name


@dataclass
class SyncResult:
    """Result of a bridge-based sync operation."""

    success: bool
    operations: list[SyncOperation]
    errors: list[str]
    warnings: list[str]


class BridgeSync:
    """
    Adapter-agnostic bidirectional sync using bridge configuration.

    This class provides generic sync functionality that works with any tool
    adapter by using bridge configuration to resolve paths dynamically.
    """

    @beartype
    @require(lambda repo_path: repo_path.exists(), "Repository path must exist")
    @require(lambda repo_path: repo_path.is_dir(), "Repository path must be a directory")
    def __init__(self, repo_path: Path, bridge_config: BridgeConfig | None = None) -> None:
        """
        Initialize bridge sync.

        Args:
            repo_path: Path to repository root
            bridge_config: Bridge configuration (auto-detected if None)
        """
        self.repo_path = Path(repo_path).resolve()
        self.bridge_config = bridge_config

        if self.bridge_config is None:
            # Auto-detect and load bridge config
            self.bridge_config = self._load_or_generate_bridge_config()

    @beartype
    @ensure(lambda result: isinstance(result, BridgeConfig), "Must return BridgeConfig")
    def _load_or_generate_bridge_config(self) -> BridgeConfig:
        """
        Load bridge config from file or auto-generate if missing.

        Returns:
            BridgeConfig instance
        """
        from specfact_cli.utils.structure import SpecFactStructure

        bridge_path = self.repo_path / SpecFactStructure.CONFIG / "bridge.yaml"

        if bridge_path.exists():
            return BridgeConfig.load_from_file(bridge_path)

        # Auto-generate bridge config
        probe = BridgeProbe(self.repo_path)
        capabilities = probe.detect()
        bridge_config = probe.auto_generate_bridge(capabilities)
        probe.save_bridge_config(bridge_config, overwrite=False)
        return bridge_config

    @beartype
    @require(lambda self: self.bridge_config is not None, "Bridge config must be set")
    @require(lambda bundle_name: isinstance(bundle_name, str) and len(bundle_name) > 0, "Bundle name must be non-empty")
    @require(lambda feature_id: isinstance(feature_id, str) and len(feature_id) > 0, "Feature ID must be non-empty")
    @ensure(lambda result: isinstance(result, Path), "Must return Path")
    def resolve_artifact_path(self, artifact_key: str, feature_id: str, bundle_name: str) -> Path:
        """
        Resolve artifact path using bridge configuration.

        Args:
            artifact_key: Artifact key (e.g., "specification", "plan")
            feature_id: Feature identifier (e.g., "001-auth")
            bundle_name: Project bundle name (for context)

        Returns:
            Resolved Path object
        """
        if self.bridge_config is None:
            msg = "Bridge config not initialized"
            raise ValueError(msg)

        context = {
            "feature_id": feature_id,
            "bundle_name": bundle_name,
        }
        return self.bridge_config.resolve_path(artifact_key, context, base_path=self.repo_path)

    @beartype
    @require(lambda bundle_name: isinstance(bundle_name, str) and len(bundle_name) > 0, "Bundle name must be non-empty")
    @require(lambda feature_id: isinstance(feature_id, str) and len(feature_id) > 0, "Feature ID must be non-empty")
    @ensure(lambda result: isinstance(result, SyncResult), "Must return SyncResult")
    def import_artifact(
        self,
        artifact_key: str,
        feature_id: str,
        bundle_name: str,
        persona: str | None = None,
    ) -> SyncResult:
        """
        Import artifact from tool format to SpecFact project bundle.

        Args:
            artifact_key: Artifact key (e.g., "specification", "plan")
            feature_id: Feature identifier (e.g., "001-auth")
            bundle_name: Project bundle name
            persona: Persona for ownership validation (optional)

        Returns:
            SyncResult with operation details
        """
        operations: list[SyncOperation] = []
        errors: list[str] = []
        warnings: list[str] = []

        if self.bridge_config is None:
            errors.append("Bridge config not initialized")
            return SyncResult(success=False, operations=operations, errors=errors, warnings=warnings)

        try:
            # Resolve artifact path
            artifact_path = self.resolve_artifact_path(artifact_key, feature_id, bundle_name)

            if not artifact_path.exists():
                errors.append(f"Artifact not found: {artifact_path}")
                return SyncResult(success=False, operations=operations, errors=errors, warnings=warnings)

            # Conflict detection: warn that bundle will be updated
            warnings.append(
                f"Importing {artifact_key} from {artifact_path}. "
                "This will update the project bundle. Existing bundle content may be modified."
            )

            # Load project bundle
            from specfact_cli.utils.structure import SpecFactStructure

            bundle_dir = self.repo_path / SpecFactStructure.PROJECTS / bundle_name
            if not bundle_dir.exists():
                errors.append(f"Project bundle not found: {bundle_dir}")
                return SyncResult(success=False, operations=operations, errors=errors, warnings=warnings)

            project_bundle = load_project_bundle(bundle_dir, validate_hashes=False)

            # Delegate to adapter-specific parser
            if self.bridge_config.adapter == AdapterType.SPECKIT:
                self._import_speckit_artifact(artifact_key, artifact_path, project_bundle, persona)
            else:
                # Generic markdown import
                self._import_generic_markdown(artifact_key, artifact_path, project_bundle)

            # Save updated bundle
            save_project_bundle(project_bundle, bundle_dir, atomic=True)

            operations.append(
                SyncOperation(
                    artifact_key=artifact_key,
                    feature_id=feature_id,
                    direction="import",
                    bundle_name=bundle_name,
                )
            )

        except Exception as e:
            errors.append(f"Import failed: {e}")

        return SyncResult(
            success=len(errors) == 0,
            operations=operations,
            errors=errors,
            warnings=warnings,
        )

    @beartype
    def _import_speckit_artifact(
        self,
        artifact_key: str,
        artifact_path: Path,
        project_bundle: ProjectBundle,
        persona: str | None,
    ) -> None:
        """
        Import Spec-Kit artifact using existing parser.

        Args:
            artifact_key: Artifact key (e.g., "specification", "plan")
            artifact_path: Path to artifact file
            project_bundle: Project bundle to update
            persona: Persona for ownership validation (optional)
        """
        from specfact_cli.importers.speckit_scanner import SpecKitScanner

        scanner = SpecKitScanner(self.repo_path)

        # Parse based on artifact type
        if artifact_key == "specification":
            # Parse spec.md
            parsed = scanner.parse_spec_markdown(artifact_path)
            if parsed:
                # Update project bundle with parsed data
                # This would integrate with existing SpecKitConverter logic
                pass
        elif artifact_key == "plan":
            # Parse plan.md
            parsed = scanner.parse_plan_markdown(artifact_path)
            if parsed:
                # Update project bundle with parsed data
                pass
        elif artifact_key == "tasks":
            # Parse tasks.md
            parsed = scanner.parse_tasks_markdown(artifact_path)
            if parsed:
                # Update project bundle with parsed data
                pass

    @beartype
    def _import_generic_markdown(
        self,
        artifact_key: str,
        artifact_path: Path,
        project_bundle: ProjectBundle,
    ) -> None:
        """
        Import generic markdown artifact.

        Args:
            artifact_key: Artifact key
            artifact_path: Path to artifact file
            project_bundle: Project bundle to update
        """
        # Basic markdown import (placeholder for future implementation)
        # TODO: Parse markdown content and update bundle
        _ = artifact_path.read_text(encoding="utf-8")  # Placeholder for future parsing

    @beartype
    @require(lambda bundle_name: isinstance(bundle_name, str) and len(bundle_name) > 0, "Bundle name must be non-empty")
    @require(lambda feature_id: isinstance(feature_id, str) and len(feature_id) > 0, "Feature ID must be non-empty")
    @ensure(lambda result: isinstance(result, SyncResult), "Must return SyncResult")
    def export_artifact(
        self,
        artifact_key: str,
        feature_id: str,
        bundle_name: str,
        persona: str | None = None,
    ) -> SyncResult:
        """
        Export artifact from SpecFact project bundle to tool format.

        Args:
            artifact_key: Artifact key (e.g., "specification", "plan")
            feature_id: Feature identifier (e.g., "001-auth")
            bundle_name: Project bundle name
            persona: Persona for section filtering (optional)

        Returns:
            SyncResult with operation details
        """
        operations: list[SyncOperation] = []
        errors: list[str] = []
        warnings: list[str] = []

        if self.bridge_config is None:
            errors.append("Bridge config not initialized")
            return SyncResult(success=False, operations=operations, errors=errors, warnings=warnings)

        try:
            # Load project bundle
            from specfact_cli.utils.structure import SpecFactStructure

            bundle_dir = self.repo_path / SpecFactStructure.PROJECTS / bundle_name
            if not bundle_dir.exists():
                errors.append(f"Project bundle not found: {bundle_dir}")
                return SyncResult(success=False, operations=operations, errors=errors, warnings=warnings)

            project_bundle = load_project_bundle(bundle_dir, validate_hashes=False)

            # Resolve artifact path
            artifact_path = self.resolve_artifact_path(artifact_key, feature_id, bundle_name)

            # Conflict detection: warn if file exists (will be overwritten)
            if artifact_path.exists():
                warnings.append(
                    f"Target file already exists: {artifact_path}. "
                    "Will overwrite with bundle content. Use --overwrite flag to suppress this warning."
                )

            # Ensure parent directory exists
            artifact_path.parent.mkdir(parents=True, exist_ok=True)

            # Delegate to adapter-specific generator
            if self.bridge_config.adapter == AdapterType.SPECKIT:
                self._export_speckit_artifact(artifact_key, artifact_path, project_bundle, feature_id, persona)
            else:
                # Generic markdown export
                self._export_generic_markdown(artifact_key, artifact_path, project_bundle, feature_id)

            operations.append(
                SyncOperation(
                    artifact_key=artifact_key,
                    feature_id=feature_id,
                    direction="export",
                    bundle_name=bundle_name,
                )
            )

        except Exception as e:
            errors.append(f"Export failed: {e}")

        return SyncResult(
            success=len(errors) == 0,
            operations=operations,
            errors=errors,
            warnings=warnings,
        )

    @beartype
    def _export_speckit_artifact(
        self,
        artifact_key: str,
        artifact_path: Path,
        project_bundle: ProjectBundle,
        feature_id: str,
        persona: str | None,
    ) -> None:
        """
        Export Spec-Kit artifact using existing generator.

        Args:
            artifact_key: Artifact key (e.g., "specification", "plan")
            artifact_path: Path to write artifact file
            project_bundle: Project bundle to export from
            feature_id: Feature identifier
            persona: Persona for section filtering (optional)

        Note: This uses placeholder implementations. Full integration with
        SpecKitConverter will be implemented in future phases.
        """
        # Find feature in bundle (by key or by feature_id pattern)
        feature = None
        for key, feat in project_bundle.features.items():
            if key == feature_id or feature_id in key:
                feature = feat
                break

        if artifact_key == "specification":
            # Generate spec.md (PO-owned sections)
            content = self._generate_spec_markdown(feature, feature_id)
            artifact_path.write_text(content, encoding="utf-8")
        elif artifact_key == "plan":
            # Generate plan.md (Architect-owned sections)
            content = self._generate_plan_markdown(feature, feature_id)
            artifact_path.write_text(content, encoding="utf-8")
        elif artifact_key == "tasks":
            # Generate tasks.md (Developer-owned sections)
            content = self._generate_tasks_markdown(feature, feature_id)
            artifact_path.write_text(content, encoding="utf-8")

    @beartype
    def _generate_spec_markdown(self, feature: Any, feature_id: str) -> str:
        """Generate spec.md content (placeholder - will integrate with SpecKitConverter)."""
        if feature is None:
            return f"# Feature Specification: {feature_id}\n\n(Feature not found in bundle)\n"
        title = feature.title if hasattr(feature, "title") else feature_id
        return f"# Feature Specification: {title}\n\n(Generated from SpecFact bundle)\n"

    @beartype
    def _generate_plan_markdown(self, feature: Any, feature_id: str) -> str:
        """Generate plan.md content (placeholder - will integrate with SpecKitConverter)."""
        if feature is None:
            return f"# Technical Plan: {feature_id}\n\n(Feature not found in bundle)\n"
        title = feature.title if hasattr(feature, "title") else feature_id
        return f"# Technical Plan: {title}\n\n(Generated from SpecFact bundle)\n"

    @beartype
    def _generate_tasks_markdown(self, feature: Any, feature_id: str) -> str:
        """Generate tasks.md content (placeholder - will integrate with SpecKitConverter)."""
        if feature is None:
            return f"# Tasks: {feature_id}\n\n(Feature not found in bundle)\n"
        title = feature.title if hasattr(feature, "title") else feature_id
        return f"# Tasks: {title}\n\n(Generated from SpecFact bundle)\n"

    @beartype
    def _export_generic_markdown(
        self,
        artifact_key: str,
        artifact_path: Path,
        project_bundle: ProjectBundle,
        feature_id: str,
    ) -> None:
        """
        Export generic markdown artifact.

        Args:
            artifact_key: Artifact key
            artifact_path: Path to write artifact file
            project_bundle: Project bundle to export from
            feature_id: Feature identifier
        """
        # Basic markdown export (placeholder for future implementation)
        content = f"# {artifact_key}\n\nExported from SpecFact bundle: {project_bundle.bundle_name}\n"
        artifact_path.write_text(content, encoding="utf-8")

    @beartype
    @require(lambda bundle_name: isinstance(bundle_name, str) and len(bundle_name) > 0, "Bundle name must be non-empty")
    @ensure(lambda result: isinstance(result, SyncResult), "Must return SyncResult")
    def sync_bidirectional(self, bundle_name: str, feature_ids: list[str] | None = None) -> SyncResult:
        """
        Perform bidirectional sync for all artifacts.

        Args:
            bundle_name: Project bundle name
            feature_ids: List of feature IDs to sync (all if None)

        Returns:
            SyncResult with all operations
        """
        operations: list[SyncOperation] = []
        errors: list[str] = []
        warnings: list[str] = []

        if self.bridge_config is None:
            errors.append("Bridge config not initialized")
            return SyncResult(success=False, operations=operations, errors=errors, warnings=warnings)

        # Validate bridge config before sync
        probe = BridgeProbe(self.repo_path)
        validation = probe.validate_bridge(self.bridge_config)
        warnings.extend(validation["warnings"])
        errors.extend(validation["errors"])

        if errors:
            return SyncResult(success=False, operations=operations, errors=errors, warnings=warnings)

        # If feature_ids not provided, discover from bridge-resolved paths
        if feature_ids is None:
            feature_ids = self._discover_feature_ids()

        # Sync each feature
        for feature_id in feature_ids:
            # Import from tool → bundle
            for _artifact_key in ["specification", "plan", "tasks"]:
                if _artifact_key in self.bridge_config.artifacts:
                    import_result = self.import_artifact(_artifact_key, feature_id, bundle_name)
                    operations.extend(import_result.operations)
                    errors.extend(import_result.errors)
                    warnings.extend(import_result.warnings)

            # Export from bundle → tool (optional, can be controlled by flag)
            # This would be done separately via export_artifact calls

        return SyncResult(
            success=len(errors) == 0,
            operations=operations,
            errors=errors,
            warnings=warnings,
        )

    @beartype
    @require(lambda self: self.bridge_config is not None, "Bridge config must be set")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def _discover_feature_ids(self) -> list[str]:
        """
        Discover feature IDs from bridge-resolved paths.

        Returns:
            List of feature IDs found in repository
        """
        feature_ids: list[str] = []

        if self.bridge_config is None:
            return feature_ids

        # Try to discover from first artifact pattern
        if "specification" in self.bridge_config.artifacts:
            artifact = self.bridge_config.artifacts["specification"]
            # Extract base directory from pattern (e.g., "specs/{feature_id}/spec.md" -> "specs")
            pattern_parts = artifact.path_pattern.split("/")
            if len(pattern_parts) > 0:
                base_dir = self.repo_path / pattern_parts[0]
                if base_dir.exists():
                    # Find all subdirectories (potential feature IDs)
                    for item in base_dir.iterdir():
                        if item.is_dir():
                            # Check if it contains the expected artifact file
                            test_path = self.resolve_artifact_path("specification", item.name, "test")
                            if test_path.exists() or (item / "spec.md").exists():
                                feature_ids.append(item.name)

        return feature_ids
