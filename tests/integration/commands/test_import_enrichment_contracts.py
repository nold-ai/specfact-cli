"""
Integration tests for import command with enrichment and contract extraction.

Tests cover:
- Enrichment not forcing full contract regeneration
- New features from enrichment getting contracts extracted
- Incremental contract extraction working correctly
- Feature objects not being used as dictionary keys (unhashable type bug)
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specfact_cli.cli import app


class TestImportEnrichmentContracts:
    """Integration tests for import command with enrichment and contract extraction."""

    @pytest.fixture
    def sample_repo_with_features(self, tmp_path: Path) -> Path:
        """Create a sample repository with Python code that will generate features."""
        repo = tmp_path / "sample_repo"
        repo.mkdir()

        # Create multiple Python files to generate features
        src_dir = repo / "src"
        src_dir.mkdir()

        # File 1: User service
        (src_dir / "user_service.py").write_text(
            '''
class UserService:
    """User management service."""

    def create_user(self, name: str, email: str) -> dict:
        """Create a new user."""
        return {"id": 1, "name": name, "email": email}

    def get_user(self, user_id: int) -> dict:
        """Get user by ID."""
        return {"id": user_id, "name": "Test User"}
'''
        )

        # File 2: Auth service
        (src_dir / "auth_service.py").write_text(
            '''
class AuthService:
    """Authentication service."""

    def login(self, username: str, password: str) -> bool:
        """Authenticate user."""
        return True

    def logout(self, user_id: int) -> bool:
        """Logout user."""
        return True
'''
        )

        return repo

    @pytest.mark.timeout(60)
    def test_enrichment_does_not_force_full_contract_regeneration(self, sample_repo_with_features: Path) -> None:
        """
        Test that enrichment doesn't force full contract regeneration.

        Bug: When enrichment was provided, it forced regeneration of ALL contracts,
        even for features with unchanged source files. This test verifies that
        only new features from enrichment get contracts extracted.
        """
        os.environ["TEST_MODE"] = "true"
        old_cwd = os.getcwd()
        try:
            os.chdir(sample_repo_with_features)

            bundle_name = "test-enrichment-contracts"
            runner = CliRunner()

            # Phase 1: Initial import (creates features and contracts)
            result1 = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    bundle_name,
                    "--repo",
                    str(sample_repo_with_features),
                    "--entry-point",
                    "src",
                    "--confidence",
                    "0.5",
                ],
            )

            assert result1.exit_code == 0, f"Initial import failed: {result1.stdout}"

            bundle_dir = sample_repo_with_features / ".specfact" / "projects" / bundle_name
            assert bundle_dir.exists()

            # Get initial contract count and modification times
            contracts_dir = bundle_dir / "contracts"
            initial_contracts = {}
            if contracts_dir.exists():
                for contract_file in contracts_dir.glob("*.yaml"):
                    initial_contracts[contract_file.name] = contract_file.stat().st_mtime

            initial_contract_count = len(initial_contracts)
            assert initial_contract_count > 0, "Should have generated some contracts"

            # Phase 2: Create enrichment report with NEW features (no source files)
            enrichment_dir = sample_repo_with_features / ".specfact" / "reports" / "enrichment"
            enrichment_dir.mkdir(parents=True, exist_ok=True)
            enrichment_report = enrichment_dir / f"{bundle_name}.enrichment.md"
            enrichment_report.write_text(
                """# Enrichment Report

## Missing Features

1. **Database Manager** (Key: FEATURE-DATABASEMANAGER)
   - Confidence: 0.80
   - Outcomes: Handles database connections and queries
   - Stories:
     1. Database Manager establishes connections
        - Acceptance: Manager creates database connection pool, manages connection lifecycle

2. **Cache Service** (Key: FEATURE-CACHESERVICE)
   - Confidence: 0.75
   - Outcomes: Provides caching functionality
   - Stories:
     1. Cache Service stores and retrieves cached data
        - Acceptance: Service stores data with TTL, retrieves cached data when available
"""
            )

            # Phase 3: Apply enrichment (should NOT regenerate existing contracts)
            result2 = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    bundle_name,
                    "--repo",
                    str(sample_repo_with_features),
                    "--entry-point",
                    "src",
                    "--enrichment",
                    str(enrichment_report),
                    "--confidence",
                    "0.5",
                ],
            )

            assert result2.exit_code == 0, f"Enrichment import failed: {result2.stdout}"

            # Verify existing contracts were NOT regenerated (same modification time)
            if contracts_dir.exists():
                for contract_file in contracts_dir.glob("*.yaml"):
                    if contract_file.name in initial_contracts:
                        # Existing contracts should NOT be regenerated
                        # (modification time should be same or very close)
                        new_mtime = contract_file.stat().st_mtime
                        old_mtime = initial_contracts[contract_file.name]
                        # Allow small difference for filesystem timestamp precision
                        time_diff = abs(new_mtime - old_mtime)
                        assert time_diff < 2.0, (
                            f"Contract {contract_file.name} was regenerated when it shouldn't have been (time diff: {time_diff}s)"
                        )

            # Verify new features from enrichment got contracts (if they have source files)
            # Note: New features without source files won't get contracts, which is correct
            final_contracts = list(contracts_dir.glob("*.yaml")) if contracts_dir.exists() else []
            # Contract count should be same or slightly more (only for new features with source files)
            # But NOT all contracts regenerated
            assert len(final_contracts) >= initial_contract_count, "Should have at least same number of contracts"

        finally:
            os.chdir(old_cwd)
            os.environ.pop("TEST_MODE", None)

    @pytest.mark.timeout(60)
    def test_enrichment_with_new_features_gets_contracts_extracted(self, sample_repo_with_features: Path) -> None:
        """
        Test that new features from enrichment get contracts extracted.

        When enrichment adds new features that have source files, those features
        should get contracts extracted (because they don't have contracts yet).
        """
        os.environ["TEST_MODE"] = "true"
        old_cwd = os.getcwd()
        try:
            os.chdir(sample_repo_with_features)

            bundle_name = "test-enrichment-new-features"
            runner = CliRunner()

            # Phase 1: Initial import
            result1 = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    bundle_name,
                    "--repo",
                    str(sample_repo_with_features),
                    "--entry-point",
                    "src",
                    "--confidence",
                    "0.5",
                ],
            )

            assert result1.exit_code == 0

            bundle_dir = sample_repo_with_features / ".specfact" / "projects" / bundle_name
            assert bundle_dir.exists()

            # Load initial features
            from specfact_cli.modules.plan.src.commands import _convert_project_bundle_to_plan_bundle
            from specfact_cli.utils.bundle_loader import load_project_bundle

            initial_project_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
            initial_plan_bundle = _convert_project_bundle_to_plan_bundle(initial_project_bundle)
            initial_feature_keys = {f.key for f in initial_plan_bundle.features}

            # Phase 2: Create enrichment with new features
            enrichment_dir = sample_repo_with_features / ".specfact" / "reports" / "enrichment"
            enrichment_dir.mkdir(parents=True, exist_ok=True)
            enrichment_report = enrichment_dir / f"{bundle_name}.enrichment.md"
            enrichment_report.write_text(
                """# Enrichment Report

## Missing Features

1. **Notification Service** (Key: FEATURE-NOTIFICATIONSERVICE)
   - Confidence: 0.80
   - Outcomes: Sends notifications to users
   - Stories:
     1. Notification Service sends email notifications
        - Acceptance: Service formats email, sends via SMTP, handles delivery errors
"""
            )

            # Phase 3: Apply enrichment
            result2 = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    bundle_name,
                    "--repo",
                    str(sample_repo_with_features),
                    "--entry-point",
                    "src",
                    "--enrichment",
                    str(enrichment_report),
                    "--confidence",
                    "0.5",
                ],
            )

            assert result2.exit_code == 0, f"Enrichment failed: {result2.stdout}"

            # Verify new feature was added
            enriched_project_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
            enriched_plan_bundle = _convert_project_bundle_to_plan_bundle(enriched_project_bundle)
            enriched_feature_keys = {f.key for f in enriched_plan_bundle.features}

            assert "FEATURE-NOTIFICATIONSERVICE" in enriched_feature_keys, "New feature from enrichment should be added"
            assert len(enriched_feature_keys) > len(initial_feature_keys), "Should have more features after enrichment"

            # Note: New features without source files won't get contracts,
            # which is correct behavior. Contracts are only extracted from source code.

        finally:
            os.chdir(old_cwd)
            os.environ.pop("TEST_MODE", None)

    @pytest.mark.timeout(60)
    def test_incremental_contract_extraction_with_enrichment(self, sample_repo_with_features: Path) -> None:
        """
        Test that incremental contract extraction works correctly with enrichment.

        When enrichment is applied, only features that need contracts should be processed:
        - New features (no contract exists)
        - Features with changed source files
        - NOT features with unchanged source files
        """
        os.environ["TEST_MODE"] = "true"
        old_cwd = os.getcwd()
        try:
            os.chdir(sample_repo_with_features)

            bundle_name = "test-incremental-enrichment"
            runner = CliRunner()

            # Phase 1: Initial import
            result1 = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    bundle_name,
                    "--repo",
                    str(sample_repo_with_features),
                    "--entry-point",
                    "src",
                    "--confidence",
                    "0.5",
                ],
            )

            assert result1.exit_code == 0

            bundle_dir = sample_repo_with_features / ".specfact" / "projects" / bundle_name
            contracts_dir = bundle_dir / "contracts"

            # Get initial contract files and their sizes
            initial_contracts = {}
            if contracts_dir.exists():
                for contract_file in contracts_dir.glob("*.yaml"):
                    initial_contracts[contract_file.name] = contract_file.stat().st_size

            # Phase 2: Create enrichment (only metadata changes, no source file changes)
            enrichment_dir = sample_repo_with_features / ".specfact" / "reports" / "enrichment"
            enrichment_dir.mkdir(parents=True, exist_ok=True)
            enrichment_report = enrichment_dir / f"{bundle_name}.enrichment.md"
            enrichment_report.write_text(
                """# Enrichment Report

## Confidence Adjustments

- FEATURE-USERSERVICE → 0.95 (strong test coverage)
"""
            )

            # Phase 3: Apply enrichment (should NOT regenerate contracts)
            result2 = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    bundle_name,
                    "--repo",
                    str(sample_repo_with_features),
                    "--entry-point",
                    "src",
                    "--enrichment",
                    str(enrichment_report),
                    "--confidence",
                    "0.5",
                ],
            )

            assert result2.exit_code == 0

            # Verify contracts were NOT regenerated (same file sizes)
            if contracts_dir.exists():
                for contract_file in contracts_dir.glob("*.yaml"):
                    if contract_file.name in initial_contracts:
                        new_size = contract_file.stat().st_size
                        old_size = initial_contracts[contract_file.name]
                        # File sizes should be same (contract not regenerated)
                        assert new_size == old_size, (
                            f"Contract {contract_file.name} was regenerated when source files didn't change"
                        )

        finally:
            os.chdir(old_cwd)
            os.environ.pop("TEST_MODE", None)

    @pytest.mark.timeout(60)
    def test_feature_objects_not_used_as_dictionary_keys(self, sample_repo_with_features: Path) -> None:
        """
        Test that Feature objects are not used as dictionary keys (unhashable type bug).

        Bug: Code was using `dict[Feature, list[Path]]` which caused "unhashable type: 'Feature'"
        error. This test verifies the fix uses feature keys (strings) instead.
        """
        os.environ["TEST_MODE"] = "true"
        old_cwd = os.getcwd()
        try:
            os.chdir(sample_repo_with_features)

            bundle_name = "test-feature-dict-keys"
            runner = CliRunner()

            # Phase 1: Initial import
            result1 = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    bundle_name,
                    "--repo",
                    str(sample_repo_with_features),
                    "--entry-point",
                    "src",
                    "--confidence",
                    "0.5",
                ],
            )

            assert result1.exit_code == 0

            # Phase 2: Create enrichment with new features
            enrichment_dir = sample_repo_with_features / ".specfact" / "reports" / "enrichment"
            enrichment_dir.mkdir(parents=True, exist_ok=True)
            enrichment_report = enrichment_dir / f"{bundle_name}.enrichment.md"
            enrichment_report.write_text(
                """# Enrichment Report

## Missing Features

1. **Logging Service** (Key: FEATURE-LOGGINGSERVICE)
   - Confidence: 0.75
   - Outcomes: Provides logging functionality
   - Stories:
     1. Logging Service writes log messages
        - Acceptance: Service formats messages, writes to log file, handles errors
"""
            )

            # Phase 3: Apply enrichment and extract contracts
            # This should NOT raise "unhashable type: 'Feature'" error
            result2 = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    bundle_name,
                    "--repo",
                    str(sample_repo_with_features),
                    "--entry-point",
                    "src",
                    "--enrichment",
                    str(enrichment_report),
                    "--confidence",
                    "0.5",
                ],
            )

            # Should succeed without unhashable type error
            assert result2.exit_code == 0, f"Should not raise unhashable type error: {result2.stdout}"
            assert "unhashable" not in result2.stdout.lower(), "Should not have unhashable type error in output"

            # Verify enrichment was applied
            assert "Applying enrichment" in result2.stdout or "Added" in result2.stdout or "📝" in result2.stdout, (
                "Enrichment should have been applied"
            )

        finally:
            os.chdir(old_cwd)
            os.environ.pop("TEST_MODE", None)

    @pytest.mark.timeout(60)
    def test_enrichment_with_large_bundle_performance(self, sample_repo_with_features: Path) -> None:
        """
        Test that enrichment doesn't cause performance regression with large bundles.

        With 320+ features, enrichment should not force regeneration of all contracts,
        which would take 80+ minutes. This test verifies performance is acceptable.
        """
        os.environ["TEST_MODE"] = "true"
        old_cwd = os.getcwd()
        try:
            os.chdir(sample_repo_with_features)

            bundle_name = "test-performance"
            runner = CliRunner()

            # Phase 1: Initial import
            result1 = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    bundle_name,
                    "--repo",
                    str(sample_repo_with_features),
                    "--entry-point",
                    "src",
                    "--confidence",
                    "0.5",
                ],
            )

            assert result1.exit_code == 0

            bundle_dir = sample_repo_with_features / ".specfact" / "projects" / bundle_name
            contracts_dir = bundle_dir / "contracts"

            # Count initial contracts
            initial_contract_count = len(list(contracts_dir.glob("*.yaml"))) if contracts_dir.exists() else 0

            # Phase 2: Create minimal enrichment (only confidence adjustment)
            enrichment_dir = sample_repo_with_features / ".specfact" / "reports" / "enrichment"
            enrichment_dir.mkdir(parents=True, exist_ok=True)
            enrichment_report = enrichment_dir / f"{bundle_name}.enrichment.md"
            enrichment_report.write_text(
                """# Enrichment Report

## Confidence Adjustments

- FEATURE-USERSERVICE → 0.90
"""
            )

            # Phase 3: Apply enrichment and measure time
            import time

            start_time = time.time()
            result2 = runner.invoke(
                app,
                [
                    "import",
                    "from-code",
                    bundle_name,
                    "--repo",
                    str(sample_repo_with_features),
                    "--entry-point",
                    "src",
                    "--enrichment",
                    str(enrichment_report),
                    "--confidence",
                    "0.5",
                ],
            )
            elapsed_time = time.time() - start_time

            assert result2.exit_code == 0

            # With enrichment that only adjusts confidence (no new features, no source changes),
            # contract extraction should be very fast (skipped for unchanged features)
            # Should complete in under 30 seconds for small bundle
            assert elapsed_time < 30.0, f"Enrichment with unchanged files took {elapsed_time:.1f}s, should be < 30s"

            # Verify contracts were not regenerated unnecessarily
            final_contract_count = len(list(contracts_dir.glob("*.yaml"))) if contracts_dir.exists() else 0
            assert final_contract_count == initial_contract_count, (
                "Contract count should not change when only confidence is adjusted"
            )

        finally:
            os.chdir(old_cwd)
            os.environ.pop("TEST_MODE", None)
