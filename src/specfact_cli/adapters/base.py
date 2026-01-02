"""
Base interface for bridge adapters.

This module defines the BridgeAdapter interface that all tool adapters must implement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.models.bridge import BridgeConfig
from specfact_cli.models.capabilities import ToolCapabilities
from specfact_cli.models.change import ChangeProposal, ChangeTracking


class BridgeAdapter(ABC):
    """
    Base interface for all bridge adapters.

    All adapters (GitHub, Spec-Kit, Linear, Jira, etc.) must implement this interface
    to provide consistent integration with SpecFact CLI.
    """

    @beartype
    @abstractmethod
    @require(lambda repo_path: repo_path.exists(), "Repository path must exist")
    @require(lambda repo_path: repo_path.is_dir(), "Repository path must be a directory")
    @ensure(lambda result: isinstance(result, bool), "Must return bool")
    def detect(self, repo_path: Path, bridge_config: BridgeConfig | None = None) -> bool:
        """
        Detect if this adapter applies to the repository.

        Args:
            repo_path: Path to repository root
            bridge_config: Optional bridge configuration (for cross-repo detection)

        Returns:
            True if adapter applies to this repository, False otherwise
        """

    @beartype
    @abstractmethod
    @require(lambda repo_path: repo_path.exists(), "Repository path must exist")
    @require(lambda repo_path: repo_path.is_dir(), "Repository path must be a directory")
    @ensure(lambda result: isinstance(result, ToolCapabilities), "Must return ToolCapabilities")
    def get_capabilities(self, repo_path: Path, bridge_config: BridgeConfig | None = None) -> ToolCapabilities:
        """
        Get tool capabilities for detected repository.

        This method is called after detect() returns True to provide detailed
        information about the tool's capabilities and configuration.

        Args:
            repo_path: Path to repository root
            bridge_config: Optional bridge configuration (for cross-repo detection)

        Returns:
            ToolCapabilities instance with tool information
        """

    @beartype
    @abstractmethod
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
        Import artifact from tool format to SpecFact.

        Args:
            artifact_key: Artifact key (e.g., "specification", "plan", "change_proposal")
            artifact_path: Path to artifact file or dict for API-based artifacts
            project_bundle: Project bundle to update
            bridge_config: Bridge configuration (may contain adapter-specific settings)
        """

    @beartype
    @abstractmethod
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
        Export artifact from SpecFact to tool format.

        Args:
            artifact_key: Artifact key (e.g., "change_proposal", "change_status")
            artifact_data: Data to export (Feature, ChangeProposal, etc.)
            bridge_config: Bridge configuration (may contain adapter-specific settings)

        Returns:
            Path to exported file or dict with API response data
        """

    @beartype
    @abstractmethod
    @require(lambda repo_path: repo_path.exists(), "Repository path must exist")
    @require(lambda repo_path: repo_path.is_dir(), "Repository path must be a directory")
    @ensure(lambda result: isinstance(result, BridgeConfig), "Must return BridgeConfig")
    def generate_bridge_config(self, repo_path: Path) -> BridgeConfig:
        """
        Generate bridge configuration for this adapter.

        Args:
            repo_path: Path to repository root

        Returns:
            BridgeConfig instance for this adapter
        """

    @beartype
    @abstractmethod
    @require(lambda bundle_dir: isinstance(bundle_dir, Path), "Bundle directory must be Path")
    @require(lambda bundle_dir: bundle_dir.exists(), "Bundle directory must exist")
    @ensure(lambda result: result is None or isinstance(result, ChangeTracking), "Must return ChangeTracking or None")
    def load_change_tracking(
        self, bundle_dir: Path, bridge_config: BridgeConfig | None = None
    ) -> ChangeTracking | None:
        """
        Load change tracking (adapter-specific storage location).

        Adapters must check `bridge_config.external_base_path` for cross-repository
        support. All paths should be resolved relative to external base when provided.

        Args:
            bundle_dir: Path to bundle directory
            bridge_config: Optional bridge configuration (for cross-repo support)

        Returns:
            ChangeTracking instance if found, None otherwise
        """

    @beartype
    @abstractmethod
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
        Save change tracking (adapter-specific storage location).

        Adapters must check `bridge_config.external_base_path` for cross-repository
        support. All paths should be resolved relative to external base when provided.

        Args:
            bundle_dir: Path to bundle directory
            change_tracking: ChangeTracking instance to save
            bridge_config: Optional bridge configuration (for cross-repo support)
        """

    @beartype
    @abstractmethod
    @require(lambda bundle_dir: isinstance(bundle_dir, Path), "Bundle directory must be Path")
    @require(lambda bundle_dir: bundle_dir.exists(), "Bundle directory must exist")
    @require(lambda change_name: isinstance(change_name, str) and len(change_name) > 0, "Change name must be non-empty")
    @ensure(lambda result: result is None or isinstance(result, ChangeProposal), "Must return ChangeProposal or None")
    def load_change_proposal(
        self, bundle_dir: Path, change_name: str, bridge_config: BridgeConfig | None = None
    ) -> ChangeProposal | None:
        """
        Load change proposal (adapter-specific storage location).

        Adapters must check `bridge_config.external_base_path` for cross-repository
        support. All paths should be resolved relative to external base when provided.

        Args:
            bundle_dir: Path to bundle directory
            change_name: Change identifier
            bridge_config: Optional bridge configuration (for cross-repo support)

        Returns:
            ChangeProposal instance if found, None otherwise
        """

    @beartype
    @abstractmethod
    @require(lambda bundle_dir: isinstance(bundle_dir, Path), "Bundle directory must be Path")
    @require(lambda bundle_dir: bundle_dir.exists(), "Bundle directory must exist")
    @require(lambda proposal: isinstance(proposal, ChangeProposal), "Proposal must be ChangeProposal")
    @ensure(lambda result: result is None, "Must return None")
    def save_change_proposal(
        self, bundle_dir: Path, proposal: ChangeProposal, bridge_config: BridgeConfig | None = None
    ) -> None:
        """
        Save change proposal (adapter-specific storage location).

        Adapters must check `bridge_config.external_base_path` for cross-repository
        support. All paths should be resolved relative to external base when provided.

        Args:
            bundle_dir: Path to bundle directory
            proposal: ChangeProposal instance to save
            bridge_config: Optional bridge configuration (for cross-repo support)
        """
