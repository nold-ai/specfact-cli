"""
OpenSpec bridge adapter for specification anchoring and delta tracking.

This adapter implements the BridgeAdapter interface to sync OpenSpec artifacts
with SpecFact, enabling validation of extracted specs against OpenSpec's
source-of-truth specifications.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.adapters.base import BridgeAdapter
from specfact_cli.adapters.openspec_parser import OpenSpecParser
from specfact_cli.models.bridge import BridgeConfig
from specfact_cli.models.capabilities import ToolCapabilities
from specfact_cli.models.change import ChangeProposal, ChangeTracking, ChangeType, FeatureDelta
from specfact_cli.models.plan import Feature
from specfact_cli.models.source_tracking import SourceTracking


class OpenSpecAdapter(BridgeAdapter):
    """
    OpenSpec bridge adapter implementing BridgeAdapter interface.

    This adapter provides read-only sync (OpenSpec → SpecFact) for Phase 1,
    enabling validation of extracted specs against OpenSpec's source-of-truth
    specifications. Future phases will add bidirectional sync and sidecar integration.
    """

    def __init__(self) -> None:
        """Initialize OpenSpec adapter."""
        self.parser = OpenSpecParser()

    @beartype
    @require(lambda repo_path: repo_path.exists(), "Repository path must exist")
    @require(lambda repo_path: repo_path.is_dir(), "Repository path must be a directory")
    @ensure(lambda result: isinstance(result, bool), "Must return bool")
    def detect(self, repo_path: Path, bridge_config: BridgeConfig | None = None) -> bool:
        """
        Detect if this is an OpenSpec repository.

        Args:
            repo_path: Path to repository root
            bridge_config: Optional bridge configuration (for cross-repo detection)

        Returns:
            True if OpenSpec structure detected, False otherwise
        """
        # Check for cross-repo OpenSpec
        base_path = repo_path
        if bridge_config and bridge_config.external_base_path:
            base_path = bridge_config.external_base_path

        # Check for OpenSpec structure (OPSX: config.yaml; legacy: project.md; or specs dir)
        config_yaml = base_path / "openspec" / "config.yaml"
        project_md = base_path / "openspec" / "project.md"
        specs_dir = base_path / "openspec" / "specs"

        return config_yaml.exists() or project_md.exists() or (specs_dir.exists() and specs_dir.is_dir())

    @beartype
    @require(lambda repo_path: repo_path.exists(), "Repository path must exist")
    @require(lambda repo_path: repo_path.is_dir(), "Repository path must be a directory")
    @ensure(lambda result: isinstance(result, ToolCapabilities), "Must return ToolCapabilities")
    def get_capabilities(self, repo_path: Path, bridge_config: BridgeConfig | None = None) -> ToolCapabilities:
        """
        Get OpenSpec adapter capabilities.

        Args:
            repo_path: Path to repository root
            bridge_config: Optional bridge configuration (for cross-repo detection)

        Returns:
            ToolCapabilities instance for OpenSpec adapter
        """
        base_path = repo_path
        if bridge_config and bridge_config.external_base_path:
            base_path = bridge_config.external_base_path

        # Check for active changes
        has_custom_hooks = len(self.parser.list_active_changes(base_path)) > 0

        return ToolCapabilities(
            tool="openspec",
            version=None,  # OpenSpec version not tracked in files
            layout="openspec",  # OpenSpec layout
            specs_dir="openspec/specs",
            has_external_config=bridge_config is not None and bridge_config.external_base_path is not None,
            has_custom_hooks=has_custom_hooks,
            supported_sync_modes=["read-only"],  # Phase 1: read-only sync
        )

    @beartype
    @require(
        lambda artifact_key: isinstance(artifact_key, str) and len(artifact_key) > 0, "Artifact key must be non-empty"
    )
    @ensure(lambda result: result is None, "Must return None")
    def import_artifact(
        self,
        artifact_key: str,
        artifact_path: Path | dict[str, Any],
        project_bundle: Any,  # ProjectBundle - avoid circular import
        bridge_config: BridgeConfig | None = None,
    ) -> None:
        """
        Import artifact from OpenSpec format to SpecFact.

        Args:
            artifact_key: Artifact key (e.g., "specification", "project_context", "change_proposal")
            artifact_path: Path to artifact file
            project_bundle: Project bundle to update
            bridge_config: Bridge configuration (may contain external_base_path)
        """
        if not isinstance(artifact_path, Path):
            msg = f"OpenSpec adapter requires Path, got {type(artifact_path)}"
            raise ValueError(msg)

        base_path = artifact_path.parent.parent.parent if bridge_config and bridge_config.external_base_path else None

        # Parse based on artifact key
        if artifact_key == "specification":
            self._import_specification(artifact_path, project_bundle, bridge_config, base_path)
        elif artifact_key == "project_context":
            self._import_project_context(artifact_path, project_bundle, bridge_config, base_path)
        elif artifact_key == "change_proposal":
            self._import_change_proposal(artifact_path, project_bundle, bridge_config, base_path)
        elif artifact_key == "change_spec_delta":
            self._import_change_spec_delta(artifact_path, project_bundle, bridge_config, base_path)
        else:
            msg = f"Unsupported artifact key: {artifact_key}"
            raise ValueError(msg)

    @beartype
    @require(
        lambda artifact_key: isinstance(artifact_key, str) and len(artifact_key) > 0, "Artifact key must be non-empty"
    )
    @ensure(lambda result: isinstance(result, (Path, dict)), "Must return Path or dict")
    def export_artifact(
        self,
        artifact_key: str,
        artifact_data: Any,  # Feature, ChangeProposal, etc. - avoid circular import
        bridge_config: BridgeConfig | None = None,
    ) -> Path | dict[str, Any]:
        """
        Export artifact from SpecFact to OpenSpec format (stub for Phase 1).

        Args:
            artifact_key: Artifact key
            artifact_data: Data to export
            bridge_config: Bridge configuration

        Returns:
            Path to exported file or dict with API response data

        Raises:
            NotImplementedError: Phase 1 is read-only
        """
        msg = "OpenSpec adapter export is not implemented in Phase 1 (read-only sync). Use Phase 4 for bidirectional sync."
        raise NotImplementedError(msg)

    @beartype
    @require(lambda repo_path: repo_path.exists(), "Repository path must exist")
    @require(lambda repo_path: repo_path.is_dir(), "Repository path must be a directory")
    @ensure(lambda result: isinstance(result, BridgeConfig), "Must return BridgeConfig")
    def generate_bridge_config(self, repo_path: Path) -> BridgeConfig:
        """
        Generate bridge configuration for OpenSpec.

        Args:
            repo_path: Path to repository root

        Returns:
            BridgeConfig instance for OpenSpec
        """
        config = BridgeConfig.preset_openspec()

        # Check if OpenSpec is in external repo (OPSX: config.yaml; legacy: project.md)
        openspec_dir = repo_path / "openspec"
        if not (openspec_dir / "config.yaml").exists() and not (openspec_dir / "project.md").exists():
            # Try to find external OpenSpec (this is a simple heuristic)
            # In practice, external_base_path should be provided via CLI option
            pass

        return config

    @beartype
    @require(lambda bundle_dir: isinstance(bundle_dir, Path), "Bundle directory must be Path")
    @require(lambda bundle_dir: bundle_dir.exists(), "Bundle directory must exist")
    @ensure(lambda result: result is None or isinstance(result, ChangeTracking), "Must return ChangeTracking or None")
    def load_change_tracking(
        self, bundle_dir: Path, bridge_config: BridgeConfig | None = None
    ) -> ChangeTracking | None:
        """
        Load change tracking from OpenSpec changes directory.

        Args:
            bundle_dir: Path to bundle directory
            bridge_config: Optional bridge configuration (for cross-repo support)

        Returns:
            ChangeTracking instance if found, None otherwise
        """
        # Determine base path for OpenSpec
        repo_path = bundle_dir.parent.parent.parent  # Navigate from .specfact/projects/{bundle}/
        base_path = (
            bridge_config.external_base_path if bridge_config and bridge_config.external_base_path else repo_path
        )

        # List active changes
        change_names = self.parser.list_active_changes(base_path)
        if not change_names:
            return None

        # Load all change proposals
        proposals: dict[str, ChangeProposal] = {}
        feature_deltas: dict[str, list[FeatureDelta]] = {}

        for change_name in change_names:
            proposal = self.load_change_proposal(bundle_dir, change_name, bridge_config)
            if proposal:
                proposals[change_name] = proposal

                # Load feature deltas for this change
                deltas = self._load_feature_deltas(base_path, change_name, bridge_config)
                if deltas:
                    feature_deltas[change_name] = deltas

        if not proposals:
            return None

        return ChangeTracking(proposals=proposals, feature_deltas=feature_deltas)

    @beartype
    @require(lambda bundle_dir: isinstance(bundle_dir, Path), "Bundle directory must be Path")
    @require(lambda bundle_dir: bundle_dir.exists(), "Bundle directory must exist")
    @require(
        lambda change_tracking: isinstance(change_tracking, ChangeTracking), "Change tracking must be ChangeTracking"
    )
    @ensure(lambda result: result is None, "Must return None")
    def save_change_tracking(
        self, bundle_dir: Path, change_tracking: ChangeTracking, bridge_config: BridgeConfig | None = None
    ) -> None:
        """
        Save change tracking to OpenSpec (stub for Phase 1).

        Args:
            bundle_dir: Path to bundle directory
            change_tracking: ChangeTracking instance to save
            bridge_config: Optional bridge configuration

        Raises:
            NotImplementedError: Phase 1 is read-only
        """
        msg = "OpenSpec adapter save_change_tracking is not implemented in Phase 1 (read-only sync). Use Phase 4 for bidirectional sync."
        raise NotImplementedError(msg)

    @beartype
    @require(lambda bundle_dir: isinstance(bundle_dir, Path), "Bundle directory must be Path")
    @require(lambda bundle_dir: bundle_dir.exists(), "Bundle directory must exist")
    @require(lambda change_name: isinstance(change_name, str) and len(change_name) > 0, "Change name must be non-empty")
    @ensure(lambda result: result is None or isinstance(result, ChangeProposal), "Must return ChangeProposal or None")
    def load_change_proposal(
        self, bundle_dir: Path, change_name: str, bridge_config: BridgeConfig | None = None
    ) -> ChangeProposal | None:
        """
        Load change proposal from OpenSpec.

        Args:
            bundle_dir: Path to bundle directory
            change_name: Change identifier
            bridge_config: Optional bridge configuration (for cross-repo support)

        Returns:
            ChangeProposal instance if found, None otherwise
        """
        # Determine base path for OpenSpec
        repo_path = bundle_dir.parent.parent.parent  # Navigate from .specfact/projects/{bundle}/
        base_path = (
            bridge_config.external_base_path if bridge_config and bridge_config.external_base_path else repo_path
        )

        proposal_path = base_path / "openspec" / "changes" / change_name / "proposal.md"
        if not proposal_path.exists():
            return None

        # Parse proposal
        parsed = self.parser.parse_change_proposal(proposal_path)

        if not parsed:
            return None  # File doesn't exist or parse error

        # Map to ChangeProposal model
        openspec_path = f"openspec/changes/{change_name}/proposal.md"
        source_metadata = {
            "openspec_path": openspec_path,
            "openspec_type": "change_proposal",
        }
        if bridge_config and bridge_config.external_base_path:
            source_metadata["openspec_base_path"] = str(bridge_config.external_base_path)

        # Use summary for title if available, otherwise use what_changes or change_name
        title = change_name
        if parsed.get("summary"):
            title = parsed["summary"].split("\n")[0] if isinstance(parsed["summary"], str) else str(parsed["summary"])
        elif parsed.get("what_changes"):
            title = (
                parsed["what_changes"].split("\n")[0]
                if isinstance(parsed["what_changes"], str)
                else str(parsed["what_changes"])
            )

        # Use rationale if available, otherwise use why
        rationale = parsed.get("rationale", "") or parsed.get("why", "")
        description = parsed.get("what_changes", "") or parsed.get("summary", "")

        return ChangeProposal(
            name=change_name,
            title=title,
            description=description,
            rationale=rationale,
            timeline=None,  # OpenSpec doesn't have timeline in proposal.md
            owner=None,
            stakeholders=[],
            dependencies=[],
            status="proposed",  # Default status
            created_at=datetime.now(UTC).isoformat(),
            applied_at=None,
            archived_at=None,
            source_tracking=SourceTracking(
                tool="openspec",
                source_metadata=source_metadata,
            ),
        )

    @beartype
    @require(lambda bundle_dir: isinstance(bundle_dir, Path), "Bundle directory must be Path")
    @require(lambda bundle_dir: bundle_dir.exists(), "Bundle directory must exist")
    @require(lambda proposal: isinstance(proposal, ChangeProposal), "Proposal must be ChangeProposal")
    @ensure(lambda result: result is None, "Must return None")
    def save_change_proposal(
        self, bundle_dir: Path, proposal: ChangeProposal, bridge_config: BridgeConfig | None = None
    ) -> None:
        """
        Save change proposal to OpenSpec (stub for Phase 1).

        Args:
            bundle_dir: Path to bundle directory
            proposal: ChangeProposal instance to save
            bridge_config: Optional bridge configuration

        Raises:
            NotImplementedError: Phase 1 is read-only
        """
        msg = "OpenSpec adapter save_change_proposal is not implemented in Phase 1 (read-only sync). Use Phase 4 for bidirectional sync."
        raise NotImplementedError(msg)

    def _import_specification(
        self,
        spec_path: Path,
        project_bundle: Any,  # ProjectBundle
        bridge_config: BridgeConfig | None,
        base_path: Path | None,
    ) -> None:
        """Import specification from OpenSpec spec.md."""
        parsed = self.parser.parse_spec_md(spec_path)

        # Extract feature ID from path (e.g., openspec/specs/001-auth/spec.md -> 001-auth)
        feature_id = spec_path.parent.name

        # Find or create feature
        feature = self._find_or_create_feature(project_bundle, feature_id)

        # Extract feature title from markdown header (# Title) if available
        if parsed and parsed.get("raw_content"):
            content = parsed["raw_content"]
            for line in content.splitlines():
                if line.startswith("# ") and not line.startswith("##"):
                    # Found main title
                    title = line.lstrip("#").strip()
                    if title:
                        feature.title = title
                        break

        # Update feature description from overview if available
        if parsed and parsed.get("overview"):
            overview_text = parsed["overview"] if isinstance(parsed["overview"], str) else str(parsed["overview"])
            # Store overview as description or in outcomes
            if overview_text and not feature.outcomes:
                feature.outcomes = [overview_text]

        # Update feature with parsed content
        if parsed and parsed.get("requirements"):
            # Add requirements to feature outcomes or acceptance criteria
            if not feature.outcomes:
                feature.outcomes = parsed["requirements"]
            else:
                feature.outcomes.extend(parsed["requirements"])

        # Store OpenSpec path in source_tracking
        openspec_path = str(spec_path.relative_to(base_path)) if base_path else f"openspec/specs/{feature_id}/spec.md"
        source_metadata = {
            "path": openspec_path,  # Test expects "path"
            "openspec_path": openspec_path,
            "openspec_type": "specification",
        }
        if bridge_config and bridge_config.external_base_path:
            source_metadata["openspec_base_path"] = str(bridge_config.external_base_path)

        if not feature.source_tracking:
            feature.source_tracking = SourceTracking(tool="openspec", source_metadata=source_metadata)
        else:
            feature.source_tracking.source_metadata.update(source_metadata)

    def _import_project_context(
        self,
        project_md_path: Path,
        project_bundle: Any,  # ProjectBundle
        bridge_config: BridgeConfig | None,
        base_path: Path | None,
    ) -> None:
        """Import project context from OpenSpec project.md (legacy) or config.yaml (OPSX)."""
        from specfact_cli.models.plan import Idea

        if project_md_path.name == "config.yaml" or project_md_path.suffix in (".yaml", ".yml"):
            parsed = self.parser.parse_config_yaml(project_md_path)
        else:
            parsed = self.parser.parse_project_md(project_md_path)

        # Create Idea if it doesn't exist
        if not hasattr(project_bundle, "idea") or project_bundle.idea is None:
            project_bundle.idea = Idea(
                title="Project",
                narrative="",
                target_users=[],
                value_hypothesis="",
                constraints=[],
                metrics=None,
            )

        # Update idea with parsed content
        if parsed:
            # Use purpose as narrative
            if parsed.get("purpose"):
                purpose_list = parsed["purpose"] if isinstance(parsed["purpose"], list) else [parsed["purpose"]]
                project_bundle.idea.narrative = "\n".join(purpose_list) if purpose_list else ""

            # Use context as additional narrative
            if parsed.get("context"):
                context_list = parsed["context"] if isinstance(parsed["context"], list) else [parsed["context"]]
                if project_bundle.idea.narrative:
                    project_bundle.idea.narrative += "\n\n" + "\n".join(context_list)
                else:
                    project_bundle.idea.narrative = "\n".join(context_list)

        # Store OpenSpec path in source_tracking (if bundle has source_tracking)
        openspec_path = str(project_md_path.relative_to(base_path if base_path else project_md_path.parent))
        source_metadata = {
            "openspec_path": openspec_path,
            "openspec_type": "project_context",
        }
        if bridge_config and bridge_config.external_base_path:
            source_metadata["openspec_base_path"] = str(bridge_config.external_base_path)

        # Note: ProjectBundle doesn't have source_tracking, so we store this in bundle metadata if available

    def _import_change_proposal(
        self,
        proposal_path: Path,
        project_bundle: Any,  # ProjectBundle
        bridge_config: BridgeConfig | None,
        base_path: Path | None,
    ) -> None:
        """Import change proposal from OpenSpec."""
        # This is handled by load_change_proposal, but we can also import directly
        change_name = proposal_path.parent.name
        proposal = self.load_change_proposal(
            project_bundle.bundle_dir if hasattr(project_bundle, "bundle_dir") else Path("."),
            change_name,
            bridge_config,
        )

        if proposal and hasattr(project_bundle, "change_tracking"):
            if not project_bundle.change_tracking:
                project_bundle.change_tracking = ChangeTracking()
            project_bundle.change_tracking.proposals[change_name] = proposal

    def _import_change_spec_delta(
        self,
        delta_path: Path,
        project_bundle: Any,  # ProjectBundle
        bridge_config: BridgeConfig | None,
        base_path: Path | None,
    ) -> None:
        """Import change spec delta from OpenSpec."""
        parsed = self.parser.parse_change_spec_delta(delta_path)

        if not parsed:
            return  # File doesn't exist or parse error

        # Extract change name and feature ID from path
        # Path: openspec/changes/{change_name}/specs/{feature_id}/spec.md
        change_name = delta_path.parent.parent.name
        feature_id = delta_path.parent.name

        # Find or get the feature for the delta
        feature = self._find_or_create_feature(project_bundle, feature_id)

        # Determine change type
        change_type_str = parsed.get("type", "MODIFIED")  # Use "type" not "change_type"
        change_type_map = {
            "ADDED": ChangeType.ADDED,
            "MODIFIED": ChangeType.MODIFIED,
            "REMOVED": ChangeType.REMOVED,
        }
        change_type = change_type_map.get(change_type_str.upper(), ChangeType.MODIFIED)

        # Create FeatureDelta based on change type
        openspec_path = str(delta_path.relative_to(base_path if base_path else delta_path.parent.parent.parent))
        source_metadata = {
            "openspec_path": openspec_path,
            "openspec_type": "change_spec_delta",
        }
        if bridge_config and bridge_config.external_base_path:
            source_metadata["openspec_base_path"] = str(bridge_config.external_base_path)

        source_tracking = SourceTracking(tool="openspec", source_metadata=source_metadata)

        if change_type == ChangeType.ADDED:
            # For ADDED, we need proposed_feature
            proposed_feature = Feature(
                key=feature_id,
                title=feature_id.replace("-", " ").title(),
                outcomes=[parsed.get("content", "")] if parsed.get("content") else [],
            )
            feature_delta = FeatureDelta(
                feature_key=feature_id,
                change_type=change_type,
                original_feature=None,
                proposed_feature=proposed_feature,
                change_rationale=None,
                change_date=datetime.now(UTC).isoformat(),
                validation_status=None,
                validation_results=None,
                source_tracking=source_tracking,
            )
        elif change_type == ChangeType.MODIFIED:
            # For MODIFIED, we need both original and proposed
            original_feature = Feature(
                key=feature_id,
                title=feature.title if hasattr(feature, "title") else feature_id.replace("-", " ").title(),
                outcomes=feature.outcomes if hasattr(feature, "outcomes") else [],
            )
            proposed_feature = Feature(
                key=feature_id,
                title=feature.title if hasattr(feature, "title") else feature_id.replace("-", " ").title(),
                outcomes=[parsed.get("content", "")] if parsed.get("content") else [],
            )
            feature_delta = FeatureDelta(
                feature_key=feature_id,
                change_type=change_type,
                original_feature=original_feature,
                proposed_feature=proposed_feature,
                change_rationale=None,
                change_date=datetime.now(UTC).isoformat(),
                validation_status=None,
                validation_results=None,
                source_tracking=source_tracking,
            )
        else:  # REMOVED
            # For REMOVED, we need original_feature
            original_feature = Feature(
                key=feature_id,
                title=feature.title if hasattr(feature, "title") else feature_id.replace("-", " ").title(),
                outcomes=feature.outcomes if hasattr(feature, "outcomes") else [],
            )
            feature_delta = FeatureDelta(
                feature_key=feature_id,
                change_type=change_type,
                original_feature=original_feature,
                proposed_feature=None,
                change_rationale=None,
                change_date=datetime.now(UTC).isoformat(),
                validation_status=None,
                validation_results=None,
                source_tracking=source_tracking,
            )

        # Add to change tracking
        if hasattr(project_bundle, "change_tracking"):
            if not project_bundle.change_tracking:
                project_bundle.change_tracking = ChangeTracking()
            if change_name not in project_bundle.change_tracking.feature_deltas:
                project_bundle.change_tracking.feature_deltas[change_name] = []
            project_bundle.change_tracking.feature_deltas[change_name].append(feature_delta)

    @beartype
    @require(lambda repo_path: repo_path.exists(), "Repository path must exist")
    @require(lambda repo_path: repo_path.is_dir(), "Repository path must be a directory")
    def discover_features(self, repo_path: Path, bridge_config: BridgeConfig | None = None) -> list[dict[str, Any]]:
        """
        Discover features from OpenSpec repository.

        This is a public helper method for sync operations to discover features
        without directly instantiating the parser.

        Args:
            repo_path: Path to repository root
            bridge_config: Optional bridge configuration (for cross-repo support)

        Returns:
            List of feature dictionaries with 'feature_key' and other metadata
        """
        base_path = repo_path
        if bridge_config and bridge_config.external_base_path:
            base_path = bridge_config.external_base_path

        features: list[dict[str, Any]] = []
        specs_dir = base_path / "openspec" / "specs"

        if not specs_dir.exists() or not specs_dir.is_dir():
            return features

        # Scan for feature directories
        for feature_dir in specs_dir.iterdir():
            if not feature_dir.is_dir():
                continue

            spec_path = feature_dir / "spec.md"
            if not spec_path.exists():
                continue

            # Extract feature ID from directory name
            feature_id = feature_dir.name

            # Parse spec to get title
            parsed = self.parser.parse_spec_md(spec_path)
            title = feature_id.replace("-", " ").title()
            if parsed and parsed.get("raw_content"):
                content = parsed["raw_content"]
                for line in content.splitlines():
                    if line.startswith("# ") and not line.startswith("##"):
                        title = line.lstrip("#").strip()
                        break

            # Create feature dictionary
            feature_dict: dict[str, Any] = {
                "feature_key": feature_id,
                "key": feature_id,  # Alias for compatibility
                "feature_title": title,
                "spec_path": str(spec_path.relative_to(base_path)),
                "openspec_path": f"openspec/specs/{feature_id}/spec.md",
            }

            # Add parsed content if available
            if parsed:
                if parsed.get("overview"):
                    feature_dict["overview"] = parsed["overview"]
                if parsed.get("requirements"):
                    feature_dict["requirements"] = parsed["requirements"]

            features.append(feature_dict)

        return features

    def _find_or_create_feature(self, project_bundle: Any, feature_id: str) -> Feature:  # ProjectBundle
        """Find existing feature or create new one."""
        if hasattr(project_bundle, "features") and project_bundle.features:
            # features is a dict[str, Feature]
            if isinstance(project_bundle.features, dict):
                if feature_id in project_bundle.features:
                    return project_bundle.features[feature_id]
            else:
                # Fallback for list (shouldn't happen but handle gracefully)
                for feature in project_bundle.features:
                    if hasattr(feature, "key") and feature.key == feature_id:
                        return feature

        # Create new feature
        feature = Feature(
            key=feature_id,
            title=feature_id.replace("-", " ").title(),
            outcomes=[],
            acceptance=[],
            constraints=[],
            stories=[],
        )

        if hasattr(project_bundle, "features"):
            if project_bundle.features is None:
                project_bundle.features = {}
            # features is a dict[str, Feature]
            if isinstance(project_bundle.features, dict):
                project_bundle.features[feature_id] = feature
            else:
                # Fallback for list (shouldn't happen but handle gracefully)
                if not hasattr(project_bundle.features, "append"):
                    project_bundle.features = {}
                    project_bundle.features[feature_id] = feature
                else:
                    project_bundle.features.append(feature)

        return feature

    def _load_feature_deltas(
        self, base_path: Path, change_name: str, bridge_config: BridgeConfig | None
    ) -> list[FeatureDelta]:
        """Load feature deltas for a change."""
        deltas: list[FeatureDelta] = []
        change_specs_dir = base_path / "openspec" / "changes" / change_name / "specs"

        if not change_specs_dir.exists():
            return deltas

        for feature_dir in change_specs_dir.iterdir():
            if feature_dir.is_dir():
                spec_path = feature_dir / "spec.md"
                if spec_path.exists():
                    parsed = self.parser.parse_change_spec_delta(spec_path)
                    if not parsed:
                        continue  # Skip if parse failed

                    feature_id = feature_dir.name

                    # Determine change type
                    change_type_str = parsed.get("type", "MODIFIED")  # Use "type" not "change_type"
                    change_type_map = {
                        "ADDED": ChangeType.ADDED,
                        "MODIFIED": ChangeType.MODIFIED,
                        "REMOVED": ChangeType.REMOVED,
                    }
                    change_type = change_type_map.get(change_type_str.upper(), ChangeType.MODIFIED)

                    # Create FeatureDelta based on change type
                    openspec_path = f"openspec/changes/{change_name}/specs/{feature_id}/spec.md"
                    source_metadata = {
                        "openspec_path": openspec_path,
                        "openspec_type": "change_spec_delta",
                    }
                    if bridge_config and bridge_config.external_base_path:
                        source_metadata["openspec_base_path"] = str(bridge_config.external_base_path)

                    source_tracking = SourceTracking(tool="openspec", source_metadata=source_metadata)

                    if change_type == ChangeType.ADDED:
                        proposed_feature = Feature(
                            key=feature_id,
                            title=feature_id.replace("-", " ").title(),
                            outcomes=[parsed.get("content", "")] if parsed.get("content") else [],
                        )
                        delta = FeatureDelta(
                            feature_key=feature_id,
                            change_type=change_type,
                            original_feature=None,
                            proposed_feature=proposed_feature,
                            change_rationale=None,
                            change_date=datetime.now(UTC).isoformat(),
                            validation_status=None,
                            validation_results=None,
                            source_tracking=source_tracking,
                        )
                    elif change_type == ChangeType.MODIFIED:
                        # For MODIFIED, we need both original and proposed
                        # Since we don't have the original, we'll create a minimal one
                        original_feature = Feature(
                            key=feature_id,
                            title=feature_id.replace("-", " ").title(),
                            outcomes=[],
                        )
                        proposed_feature = Feature(
                            key=feature_id,
                            title=feature_id.replace("-", " ").title(),
                            outcomes=[parsed.get("content", "")] if parsed.get("content") else [],
                        )
                        delta = FeatureDelta(
                            feature_key=feature_id,
                            change_type=change_type,
                            original_feature=original_feature,
                            proposed_feature=proposed_feature,
                            change_rationale=None,
                            change_date=datetime.now(UTC).isoformat(),
                            validation_status=None,
                            validation_results=None,
                            source_tracking=source_tracking,
                        )
                    else:  # REMOVED
                        original_feature = Feature(
                            key=feature_id,
                            title=feature_id.replace("-", " ").title(),
                            outcomes=[],
                        )
                        delta = FeatureDelta(
                            feature_key=feature_id,
                            change_type=change_type,
                            original_feature=original_feature,
                            proposed_feature=None,
                            change_rationale=None,
                            change_date=datetime.now(UTC).isoformat(),
                            validation_status=None,
                            validation_results=None,
                            source_tracking=source_tracking,
                        )
                    deltas.append(delta)

        return deltas
