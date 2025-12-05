"""
Integration tests for SpecToTestsSync - Specmatic test generation.

Tests the spec-to-tests sync workflow that generates tests from OpenAPI contracts
using Specmatic flows.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from specfact_cli.models.plan import Feature, Product
from specfact_cli.models.project import BundleManifest, ProjectBundle
from specfact_cli.sync.change_detector import SpecChange
from specfact_cli.sync.spec_to_tests import SpecToTestsSync


class TestSpecToTestsSync:
    """Test suite for SpecToTestsSync class."""

    def test_sync_specmatic_not_available(self, tmp_path: Path) -> None:
        """Test sync when Specmatic is not available."""
        sync = SpecToTestsSync("test-bundle", tmp_path)

        with patch(
            "specfact_cli.integrations.specmatic.check_specmatic_available", return_value=(False, "Not installed")
        ):
            changes = [SpecChange(feature_key="FEATURE-001", change_type="modified")]
            with pytest.raises(RuntimeError, match="Specmatic not available"):
                sync.sync(changes, "test-bundle")

    def test_sync_no_changes(self, tmp_path: Path) -> None:
        """Test sync with empty changes list."""
        # Create bundle (even with no changes, bundle needs to exist for loading)
        bundle_name = "test-bundle"
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle_dir.mkdir(parents=True)

        from specfact_cli.utils.bundle_loader import save_project_bundle

        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        project_bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)
        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        sync = SpecToTestsSync(bundle_name, tmp_path)

        with patch("specfact_cli.integrations.specmatic.check_specmatic_available", return_value=(True, None)):
            # Should complete without error
            sync.sync([], bundle_name)

    def test_sync_feature_without_contract(self, tmp_path: Path) -> None:
        """Test sync when feature has no contract."""
        # Create bundle
        bundle_name = "test-bundle"
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle_dir.mkdir(parents=True)

        from specfact_cli.utils.bundle_loader import save_project_bundle

        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        project_bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

        # Add feature without contract
        feature = Feature(
            key="FEATURE-001",
            title="Feature without contract",
            stories=[],
            source_tracking=None,
            contract=None,  # No contract
            protocol=None,
        )
        project_bundle.features["FEATURE-001"] = feature
        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        sync = SpecToTestsSync(bundle_name, tmp_path)
        changes = [SpecChange(feature_key="FEATURE-001", change_type="modified")]

        with patch("specfact_cli.integrations.specmatic.check_specmatic_available", return_value=(True, None)):
            # Should complete without error (skips features without contracts)
            sync.sync(changes, bundle_name)

    def test_sync_contract_not_found(self, tmp_path: Path) -> None:
        """Test sync when contract file doesn't exist."""
        # Create bundle
        bundle_name = "test-bundle"
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle_dir.mkdir(parents=True)

        from specfact_cli.utils.bundle_loader import save_project_bundle

        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        project_bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

        # Add feature with contract path that doesn't exist
        feature = Feature(
            key="FEATURE-001",
            title="Feature with missing contract",
            stories=[],
            source_tracking=None,
            contract="contracts/nonexistent.yaml",  # Contract doesn't exist
            protocol=None,
        )
        project_bundle.features["FEATURE-001"] = feature
        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        sync = SpecToTestsSync(bundle_name, tmp_path)
        changes = [SpecChange(feature_key="FEATURE-001", change_type="modified")]

        with patch("specfact_cli.integrations.specmatic.check_specmatic_available", return_value=(True, None)):
            # Should complete without error (skips missing contracts)
            sync.sync(changes, bundle_name)

    def test_sync_success_with_specmatic(self, tmp_path: Path) -> None:
        """Test successful sync with Specmatic available."""
        # Create bundle
        bundle_name = "test-bundle"
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle_dir.mkdir(parents=True)

        from specfact_cli.utils.bundle_loader import save_project_bundle

        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        project_bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

        # Create contract file
        contracts_dir = bundle_dir / "contracts"
        contracts_dir.mkdir(parents=True)
        contract_file = contracts_dir / "api.yaml"
        contract_file.write_text("openapi: 3.0.0\ninfo:\n  title: Test API\n  version: 1.0.0\n")

        # Add feature with contract
        feature = Feature(
            key="FEATURE-001",
            title="Feature with contract",
            stories=[],
            source_tracking=None,
            contract="contracts/api.yaml",
            protocol=None,
        )
        project_bundle.features["FEATURE-001"] = feature
        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        sync = SpecToTestsSync(bundle_name, tmp_path)
        changes = [SpecChange(feature_key="FEATURE-001", change_type="modified")]

        with (
            patch("specfact_cli.integrations.specmatic.check_specmatic_available", return_value=(True, None)),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0)
            # Should complete successfully
            sync.sync(changes, bundle_name)

            # Verify Specmatic was called
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert call_args[0] == "specmatic"
            assert call_args[1] == "test"
            assert "--spec" in call_args
            assert str(contract_file) in call_args

    def test_sync_fallback_to_npx(self, tmp_path: Path) -> None:
        """Test sync falls back to npx when specmatic command not found."""
        # Create bundle
        bundle_name = "test-bundle"
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle_dir.mkdir(parents=True)

        from specfact_cli.utils.bundle_loader import save_project_bundle

        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        project_bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

        # Create contract file
        contracts_dir = bundle_dir / "contracts"
        contracts_dir.mkdir(parents=True)
        contract_file = contracts_dir / "api.yaml"
        contract_file.write_text("openapi: 3.0.0\ninfo:\n  title: Test API\n  version: 1.0.0\n")

        # Add feature with contract
        feature = Feature(
            key="FEATURE-001",
            title="Feature with contract",
            stories=[],
            source_tracking=None,
            contract="contracts/api.yaml",
            protocol=None,
        )
        project_bundle.features["FEATURE-001"] = feature
        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        sync = SpecToTestsSync(bundle_name, tmp_path)
        changes = [SpecChange(feature_key="FEATURE-001", change_type="modified")]

        with (
            patch("specfact_cli.integrations.specmatic.check_specmatic_available", return_value=(True, None)),
            patch("subprocess.run") as mock_run,
        ):
            # First call (specmatic) raises FileNotFoundError, second (npx) succeeds
            mock_run.side_effect = [
                FileNotFoundError(),  # specmatic not found
                MagicMock(returncode=0),  # npx specmatic works
            ]
            # Should complete successfully
            sync.sync(changes, bundle_name)

            # Verify both calls were attempted
            assert mock_run.call_count == 2
            # First call should be specmatic
            assert mock_run.call_args_list[0][0][0][0] == "specmatic"
            # Second call should be npx
            assert mock_run.call_args_list[1][0][0][0] == "npx"

    def test_sync_specmatic_failure(self, tmp_path: Path) -> None:
        """Test sync raises error when Specmatic test generation fails."""
        # Create bundle
        bundle_name = "test-bundle"
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle_dir.mkdir(parents=True)

        from specfact_cli.utils.bundle_loader import save_project_bundle

        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        project_bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

        # Create contract file
        contracts_dir = bundle_dir / "contracts"
        contracts_dir.mkdir(parents=True)
        contract_file = contracts_dir / "api.yaml"
        contract_file.write_text("openapi: 3.0.0\ninfo:\n  title: Test API\n  version: 1.0.0\n")

        # Add feature with contract
        feature = Feature(
            key="FEATURE-001",
            title="Feature with contract",
            stories=[],
            source_tracking=None,
            contract="contracts/api.yaml",
            protocol=None,
        )
        project_bundle.features["FEATURE-001"] = feature
        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        sync = SpecToTestsSync(bundle_name, tmp_path)
        changes = [SpecChange(feature_key="FEATURE-001", change_type="modified")]

        with (
            patch("specfact_cli.integrations.specmatic.check_specmatic_available", return_value=(True, None)),
            patch("subprocess.run") as mock_run,
        ):
            # Mock Specmatic failure
            import subprocess

            mock_run.side_effect = subprocess.CalledProcessError(1, "specmatic", stderr="Test failed")

            with pytest.raises(RuntimeError, match="Specmatic test generation failed"):
                sync.sync(changes, bundle_name)

    def test_sync_multiple_changes(self, tmp_path: Path) -> None:
        """Test sync with multiple specification changes."""
        # Create bundle
        bundle_name = "test-bundle"
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle_dir.mkdir(parents=True)

        from specfact_cli.utils.bundle_loader import save_project_bundle

        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        project_bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

        # Create contract files
        contracts_dir = bundle_dir / "contracts"
        contracts_dir.mkdir(parents=True)
        contract1 = contracts_dir / "api1.yaml"
        contract1.write_text("openapi: 3.0.0\ninfo:\n  title: API 1\n  version: 1.0.0\n")
        contract2 = contracts_dir / "api2.yaml"
        contract2.write_text("openapi: 3.0.0\ninfo:\n  title: API 2\n  version: 1.0.0\n")

        # Add features with contracts
        feature1 = Feature(
            key="FEATURE-001",
            title="Feature 1",
            stories=[],
            source_tracking=None,
            contract="contracts/api1.yaml",
            protocol=None,
        )
        feature2 = Feature(
            key="FEATURE-002",
            title="Feature 2",
            stories=[],
            source_tracking=None,
            contract="contracts/api2.yaml",
            protocol=None,
        )
        project_bundle.features["FEATURE-001"] = feature1
        project_bundle.features["FEATURE-002"] = feature2
        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        sync = SpecToTestsSync(bundle_name, tmp_path)
        changes = [
            SpecChange(feature_key="FEATURE-001", change_type="modified"),
            SpecChange(feature_key="FEATURE-002", change_type="modified"),
        ]

        with (
            patch("specfact_cli.integrations.specmatic.check_specmatic_available", return_value=(True, None)),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0)
            # Should complete successfully
            sync.sync(changes, bundle_name)

            # Verify Specmatic was called for each change
            assert mock_run.call_count == 2
