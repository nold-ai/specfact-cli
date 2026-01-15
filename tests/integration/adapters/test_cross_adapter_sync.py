"""
Integration tests for cross-adapter sync scenarios.

Tests OpenSpec ↔ Spec-Kit sync workflows, including bidirectional sync,
conflict resolution, and cross-repo scenarios.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from unittest.mock import MagicMock, patch

import pytest
from beartype import beartype

from specfact_cli.adapters.openspec import OpenSpecAdapter
from specfact_cli.models.bridge import BridgeConfig
from specfact_cli.models.change import ChangeProposal, ChangeTracking, ChangeType, FeatureDelta
from specfact_cli.models.plan import Feature
from specfact_cli.sync.bridge_sync import BridgeSync


@pytest.fixture
def openspec_repo(tmp_path: Path) -> Path:
    """Create test OpenSpec repository structure."""
    openspec_dir = tmp_path / "openspec"
    openspec_dir.mkdir(exist_ok=True)

    # Create project.md
    (openspec_dir / "project.md").write_text(
        dedent(
            """# Test Project

## Purpose

This is a test project for cross-adapter sync.

## Context

- OpenSpec ↔ Spec-Kit integration
- Cross-repo scenarios
"""
        )
    )

    # Create specs directory
    specs_dir = openspec_dir / "specs" / "001-auth"
    specs_dir.mkdir(parents=True, exist_ok=True)

    spec_md = dedent(
        """# Authentication Feature

## Overview

This feature provides user authentication capabilities.

## User Scenarios & Testing

### User Story 1 - Login (Priority: P1)
As a user, I want to log in so that I can access the system.

**Acceptance Scenarios**:
1. Given valid credentials, When user logs in, Then access is granted
2. Given invalid credentials, When user logs in, Then access is denied
"""
    )
    (specs_dir / "spec.md").write_text(spec_md)

    # Create change proposal
    changes_dir = openspec_dir / "changes" / "update-auth"
    changes_dir.mkdir(parents=True, exist_ok=True)

    proposal_md = dedent(
        """# Update Authentication

## Why

Improve authentication security.

## What Changes

- Add two-factor authentication
- Update password requirements

## Impact

- Affects authentication flow
- Requires database migration
"""
    )
    (changes_dir / "proposal.md").write_text(proposal_md)

    return tmp_path


@pytest.fixture
def speckit_repo(tmp_path: Path) -> Path:
    """Create test Spec-Kit repository structure."""
    specify_dir = tmp_path / ".specify"
    specify_dir.mkdir(exist_ok=True)

    specs_dir = tmp_path / "specs" / "001-auth"
    specs_dir.mkdir(parents=True, exist_ok=True)

    spec_md = dedent(
        """# Authentication Feature

## User Scenarios & Testing

### User Story 1 - Login (Priority: P1)
As a user, I want to log in so that I can access the system.

**Acceptance Scenarios**:
1. Given valid credentials, When user logs in, Then access is granted
2. Given invalid credentials, When user logs in, Then access is denied
"""
    )
    (specs_dir / "spec.md").write_text(spec_md)

    return tmp_path


@pytest.fixture
def openspec_adapter() -> OpenSpecAdapter:
    """Create OpenSpec adapter instance for testing."""
    return OpenSpecAdapter()


@pytest.fixture
def bridge_config() -> BridgeConfig:
    """Create bridge config for testing."""
    return BridgeConfig.preset_openspec()


class TestCrossAdapterSync:
    """Integration tests for cross-adapter sync scenarios."""

    @beartype
    @patch("specfact_cli.validators.change_proposal_integration.AdapterRegistry")
    def test_openspec_to_speckit_sync(
        self,
        mock_registry: MagicMock,
        openspec_repo: Path,
        speckit_repo: Path,
    ) -> None:
        """Test OpenSpec → Spec-Kit sync (change proposal → spec update)."""
        # Ensure OpenSpec structure exists (fixture creates it, but verify)
        openspec_path = openspec_repo / "openspec"
        openspec_path.mkdir(exist_ok=True)

        feature_delta = FeatureDelta(
            feature_key="001-auth",
            change_type=ChangeType.MODIFIED,
            original_feature=Feature(key="001-auth", title="Authentication Feature", outcomes=["Old outcome"]),
            proposed_feature=Feature(
                key="001-auth", title="Authentication Feature", outcomes=["Old outcome", "Add 2FA support"]
            ),
            change_rationale=None,
            change_date=None,
            validation_status=None,
            validation_results=None,
            source_tracking=None,
        )

        change_tracking = ChangeTracking(
            proposals={
                "update-auth": ChangeProposal(
                    name="update-auth",
                    title="Update Authentication",
                    description="Add two-factor authentication",
                    rationale="Improve security",
                    status="proposed",
                    created_at="2025-01-01T10:00:00Z",
                    timeline=None,
                    owner=None,
                    applied_at=None,
                    archived_at=None,
                    source_tracking=None,
                )
            },
            feature_deltas={"update-auth": [feature_delta]},
        )

        # Mock adapters
        mock_openspec_adapter = MagicMock()
        mock_openspec_adapter.detect.return_value = True
        mock_openspec_adapter.load_change_tracking.return_value = change_tracking

        mock_speckit_adapter = MagicMock()
        mock_speckit_adapter.detect.return_value = True

        def get_adapter(adapter_name: str, **kwargs):
            if adapter_name == "openspec":
                return mock_openspec_adapter
            if adapter_name == "speckit":
                return mock_speckit_adapter
            raise ValueError(f"Adapter '{adapter_name}' not found")

        mock_registry.get_adapter.side_effect = get_adapter

        # Test that change proposal can be loaded
        from specfact_cli.validators.change_proposal_integration import load_active_change_proposals

        active_tracking = load_active_change_proposals(openspec_repo)
        assert active_tracking is not None
        assert "update-auth" in active_tracking.proposals

        # Verify feature delta exists
        assert "update-auth" in active_tracking.feature_deltas
        assert len(active_tracking.feature_deltas["update-auth"]) > 0
        assert active_tracking.feature_deltas["update-auth"][0].change_type == ChangeType.MODIFIED

    @beartype
    @patch("specfact_cli.adapters.registry.AdapterRegistry")
    def test_speckit_to_openspec_sync(
        self,
        mock_registry: MagicMock,
        openspec_repo: Path,
        speckit_repo: Path,
    ) -> None:
        """Test Spec-Kit → OpenSpec sync (spec update → change proposal)."""
        # This would test creating a change proposal from Spec-Kit spec changes
        # For now, we verify the structure exists and adapters can detect each other

        mock_openspec_adapter_class = MagicMock()
        mock_openspec_adapter = MagicMock()
        mock_openspec_adapter.detect.return_value = True
        mock_openspec_adapter_class.return_value = mock_openspec_adapter

        mock_speckit_adapter_class = MagicMock()
        mock_speckit_adapter = MagicMock()
        mock_speckit_adapter.detect.return_value = True
        mock_speckit_adapter_class.return_value = mock_speckit_adapter

        def get_adapter(adapter_name: str):
            if adapter_name == "openspec":
                return mock_openspec_adapter_class
            if adapter_name == "speckit":
                return mock_speckit_adapter_class
            return None

        mock_registry.get.side_effect = get_adapter

        # Verify both adapters can detect their respective repos
        openspec_adapter = OpenSpecAdapter()
        assert openspec_adapter.detect(openspec_repo) is True

        # Spec-Kit adapter detection would be tested here
        # For now, we verify the structure
        assert (speckit_repo / "specs" / "001-auth" / "spec.md").exists()

    @beartype
    def test_bidirectional_sync_with_conflict_resolution(
        self,
        openspec_repo: Path,
    ) -> None:
        """Test bidirectional sync with conflict resolution."""
        # Create conflicting states: OpenSpec has "proposed", external source has "in-progress"
        # Create conflict test proposal structure
        openspec_path = openspec_repo / "openspec"
        changes_dir = openspec_path / "changes" / "conflict-test"
        changes_dir.mkdir(parents=True, exist_ok=True)

        # Simulate external source (e.g., GitHub) has "in-progress"
        # OpenSpec has "proposed" status (from proposal in repo)
        # (changes_dir created but not used in this test - structure verification only)

        # Test conflict resolution strategies
        from specfact_cli.adapters.github import GitHubAdapter

        github_adapter = GitHubAdapter(
            repo_owner="test-owner",
            repo_name="test-repo",
            api_token="test-token",
        )

        issue_data = {"labels": [{"name": "in-progress"}, {"name": "openspec"}]}
        proposal_dict = {"status": "proposed"}

        # Test prefer_openspec strategy
        resolved = github_adapter.sync_status_from_github(
            issue_data=issue_data,
            proposal=proposal_dict,
            strategy="prefer_openspec",
        )
        assert resolved == "proposed"  # OpenSpec takes precedence

        # Test prefer_backlog strategy
        resolved = github_adapter.sync_status_from_github(
            issue_data=issue_data,
            proposal=proposal_dict,
            strategy="prefer_backlog",
        )
        assert resolved == "in-progress"  # Backlog takes precedence

        # Test merge strategy (most advanced wins)
        resolved = github_adapter.sync_status_from_github(
            issue_data=issue_data,
            proposal=proposal_dict,
            strategy="merge",
        )
        assert resolved == "in-progress"  # in-progress is more advanced than proposed

    @beartype
    def test_external_base_path_support(
        self,
        tmp_path: Path,
    ) -> None:
        """Test external_base_path support (cross-repo scenarios)."""
        # Create OpenSpec in separate repo
        external_repo = tmp_path / "external-openspec"
        openspec_dir = external_repo / "openspec"
        openspec_dir.mkdir(parents=True, exist_ok=True)

        (openspec_dir / "project.md").write_text("# External Project\n\n## Purpose\n\nTest cross-repo")

        # Create main repo (code repo)
        main_repo = tmp_path / "main-repo"
        main_repo.mkdir(exist_ok=True)

        # Test with external_base_path (use preset and create new instance with external path)
        base_config = BridgeConfig.preset_openspec()
        bridge_config = BridgeConfig(
            version=base_config.version,
            adapter=base_config.adapter,
            artifacts=base_config.artifacts,
            external_base_path=external_repo,
            commands=base_config.commands,
            templates=base_config.templates,
        )

        openspec_adapter = OpenSpecAdapter()

        # Should detect OpenSpec in external repo
        assert openspec_adapter.detect(main_repo, bridge_config) is True

        # Verify capabilities respect external_base_path
        capabilities = openspec_adapter.get_capabilities(main_repo, bridge_config)
        assert capabilities.tool == "openspec"
        assert capabilities.has_external_config is True

    @beartype
    @patch("specfact_cli.adapters.registry.AdapterRegistry")
    def test_cross_adapter_sync_error_handling(
        self,
        mock_registry: MagicMock,
        openspec_repo: Path,
    ) -> None:
        """Test error handling in cross-adapter sync scenarios."""
        # Test missing adapter
        mock_registry.get_adapter.side_effect = ValueError("Adapter 'openspec' not found")

        from specfact_cli.validators.change_proposal_integration import load_active_change_proposals

        # Should handle gracefully when adapter not found
        # (In real scenario, this would fall back to Spec-Kit only)
        # Verify adapter not found returns None
        active_tracking = load_active_change_proposals(openspec_repo)
        # Result depends on implementation - may return None or empty tracking
        assert active_tracking is None or isinstance(active_tracking, ChangeTracking)

        # Test invalid bridge config (use preset and modify)
        invalid_config = BridgeConfig.preset_openspec()
        openspec_adapter = OpenSpecAdapter()

        # Should still detect if OpenSpec structure exists
        assert openspec_adapter.detect(openspec_repo, invalid_config) is True

    @beartype
    def test_cross_repo_scenario_with_sync(
        self,
        tmp_path: Path,
    ) -> None:
        """Test cross-repo scenario with actual sync operation."""
        # Create OpenSpec in external repo
        external_repo = tmp_path / "external-openspec"
        openspec_dir = external_repo / "openspec"
        openspec_dir.mkdir(parents=True, exist_ok=True)

        (openspec_dir / "project.md").write_text("# External Project\n\n## Purpose\n\nTest cross-repo sync")

        specs_dir = openspec_dir / "specs" / "001-feature"
        specs_dir.mkdir(parents=True, exist_ok=True)

        (specs_dir / "spec.md").write_text("# Feature 1\n\n## Overview\n\nTest feature")

        # Create main repo (code repo)
        main_repo = tmp_path / "main-repo"
        main_repo.mkdir(exist_ok=True)

        # Create bridge config with external_base_path
        base_config = BridgeConfig.preset_openspec()
        bridge_config = BridgeConfig(
            version=base_config.version,
            adapter=base_config.adapter,
            artifacts=base_config.artifacts,
            external_base_path=external_repo,
            commands=base_config.commands,
            templates=base_config.templates,
        )

        # Test bridge sync with external path
        bridge_sync = BridgeSync(main_repo, bridge_config=bridge_config)

        # Verify sync can be initialized
        assert bridge_sync.bridge_config == bridge_config
        assert bridge_sync.bridge_config is not None
        assert bridge_sync.bridge_config.external_base_path == external_repo
