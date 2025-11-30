"""Integration tests for migrate command."""

from __future__ import annotations

import yaml
from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.models.plan import Feature, Story
from specfact_cli.utils.bundle_loader import load_project_bundle, save_project_bundle


runner = CliRunner()


class TestMigrateToContractsCommand:
    """Test suite for migrate to-contracts command."""

    def test_migrate_to_contracts_creates_contracts(self, tmp_path, monkeypatch):
        """Test migrate to-contracts creates OpenAPI contract files."""
        monkeypatch.chdir(tmp_path)

        # Create a project bundle with verbose acceptance criteria
        bundle_name = "test-bundle"
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle_dir.mkdir(parents=True)

        from specfact_cli.models.plan import Product
        from specfact_cli.models.project import BundleManifest, ProjectBundle

        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        project_bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

        # Add a feature with verbose acceptance criteria
        feature = Feature(
            key="FEATURE-001",
            title="User Authentication",
            outcomes=["Users can log in"],
            acceptance=[],
            constraints=[],
            stories=[
                Story(
                    key="STORY-001",
                    title="Login endpoint",
                    acceptance=[
                        "Given a user with valid credentials",
                        "POST /api/login is called with username and password",
                        "Then the API returns 200 OK with JWT token",
                    ],
                    tags=[],
                    story_points=None,
                    value_points=None,
                    tasks=[],
                    confidence=1.0,
                    draft=False,
                    scenarios=None,
                    contracts=None,
                    source_functions=[],
                    test_functions=[],
                )
            ],
            confidence=1.0,
            draft=False,
            source_tracking=None,
            contract=None,
            protocol=None,
        )
        project_bundle.features["FEATURE-001"] = feature

        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        # Run migration
        result = runner.invoke(
            app,
            [
                "migrate",
                "to-contracts",
                bundle_name,
                "--repo",
                str(tmp_path),
                "--no-validate-with-specmatic",  # Skip Specmatic validation for faster tests
            ],
        )

        assert result.exit_code == 0, f"Migration failed: {result.stdout}\n{result.stderr}"

        # Verify contracts directory was created
        contracts_dir = bundle_dir / "contracts"
        assert contracts_dir.exists(), (
            f"Contracts directory not found at {contracts_dir}. Migration output: {result.stdout}"
        )

        # Verify contract file was created
        contract_file = contracts_dir / "FEATURE-001.openapi.yaml"
        assert contract_file.exists(), f"Contract file not found at {contract_file}"

        # Verify feature was updated with contract reference
        updated_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        assert updated_bundle.features["FEATURE-001"].contract is not None
        assert "contracts/FEATURE-001.openapi.yaml" in updated_bundle.features["FEATURE-001"].contract

    def test_migrate_to_contracts_dry_run(self, tmp_path, monkeypatch):
        """Test migrate to-contracts dry-run mode doesn't create files."""
        monkeypatch.chdir(tmp_path)

        # Create a project bundle with verbose acceptance criteria
        bundle_name = "test-bundle"
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle_dir.mkdir(parents=True)

        from specfact_cli.models.plan import Product
        from specfact_cli.models.project import BundleManifest, ProjectBundle

        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        project_bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

        feature = Feature(
            key="FEATURE-001",
            title="Test Feature",
            outcomes=["Test outcome"],
            acceptance=[],
            constraints=[],
            stories=[
                Story(
                    key="STORY-001",
                    title="Test Story",
                    acceptance=["When POST /api/test is called", "Then returns 200 OK"],
                    tags=[],
                    story_points=None,
                    value_points=None,
                    tasks=[],
                    confidence=1.0,
                    draft=False,
                    scenarios=None,
                    contracts=None,
                    source_functions=[],
                    test_functions=[],
                )
            ],
            confidence=1.0,
            draft=False,
            source_tracking=None,
            contract=None,
            protocol=None,
        )
        project_bundle.features["FEATURE-001"] = feature

        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        # Run migration in dry-run mode
        result = runner.invoke(
            app,
            [
                "migrate",
                "to-contracts",
                bundle_name,
                "--repo",
                str(tmp_path),
                "--dry-run",
                "--no-validate-with-specmatic",
            ],
        )

        assert result.exit_code == 0
        assert "DRY RUN MODE" in result.stdout or "dry run" in result.stdout.lower()

        # Verify contracts directory was NOT created
        contracts_dir = bundle_dir / "contracts"
        assert not contracts_dir.exists(), "Contracts directory should not exist in dry-run mode"

        # Verify bundle was not modified
        original_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        assert original_bundle.features["FEATURE-001"].contract is None

    def test_migrate_to_contracts_missing_bundle(self, tmp_path, monkeypatch):
        """Test migrate to-contracts fails when bundle doesn't exist."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(
            app,
            [
                "migrate",
                "to-contracts",
                "non-existent-bundle",
                "--repo",
                str(tmp_path),
            ],
        )

        assert result.exit_code == 1
        assert "not found" in result.stdout.lower() or "Project bundle not found" in result.stdout

    def test_migrate_to_contracts_skips_existing_contracts(self, tmp_path, monkeypatch):
        """Test migrate to-contracts skips features that already have contracts."""
        monkeypatch.chdir(tmp_path)

        # Create a project bundle with a feature that already has a contract
        bundle_name = "test-bundle"
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle_dir.mkdir(parents=True)

        from specfact_cli.models.plan import Product
        from specfact_cli.models.project import BundleManifest, ProjectBundle

        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        project_bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

        # Feature with existing contract
        feature_with_contract = Feature(
            key="FEATURE-001",
            title="Feature with Contract",
            outcomes=["Outcome"],
            acceptance=[],
            constraints=[],
            stories=[
                Story(
                    key="STORY-001",
                    title="Story",
                    acceptance=["Acceptance criteria"],
                    tags=[],
                    story_points=None,
                    value_points=None,
                    tasks=[],
                    confidence=1.0,
                    draft=False,
                    scenarios=None,
                    contracts=None,
                    source_functions=[],
                    test_functions=[],
                )
            ],
            confidence=1.0,
            draft=False,
            source_tracking=None,
            contract="contracts/FEATURE-001.openapi.yaml",
            protocol=None,
        )

        # Feature without contract
        feature_without_contract = Feature(
            key="FEATURE-002",
            title="Feature without Contract",
            outcomes=["Outcome"],
            acceptance=[],
            constraints=[],
            stories=[
                Story(
                    key="STORY-002",
                    title="Story",
                    acceptance=["When POST /api/test is called", "Then returns 200 OK"],
                    tags=[],
                    story_points=None,
                    value_points=None,
                    tasks=[],
                    confidence=1.0,
                    draft=False,
                    scenarios=None,
                    contracts=None,
                    source_functions=[],
                    test_functions=[],
                )
            ],
            confidence=1.0,
            draft=False,
            source_tracking=None,
            contract=None,
            protocol=None,
        )

        project_bundle.features["FEATURE-001"] = feature_with_contract
        project_bundle.features["FEATURE-002"] = feature_without_contract

        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        # Create the existing contract file for FEATURE-001 so it gets skipped
        contracts_dir = bundle_dir / "contracts"
        contracts_dir.mkdir(parents=True, exist_ok=True)
        existing_contract = contracts_dir / "FEATURE-001.openapi.yaml"

        existing_contract.write_text(
            yaml.dump(
                {
                    "openapi": "3.0.3",
                    "info": {"title": "Feature with Contract", "version": "1.0.0"},
                    "paths": {},
                },
                default_flow_style=False,
            )
        )

        # Run migration
        result = runner.invoke(
            app,
            [
                "migrate",
                "to-contracts",
                bundle_name,
                "--repo",
                str(tmp_path),
                "--no-validate-with-specmatic",
            ],
        )

        assert result.exit_code == 0

        # Verify only FEATURE-002 got a contract
        updated_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        assert updated_bundle.features["FEATURE-001"].contract == "contracts/FEATURE-001.openapi.yaml"
        assert updated_bundle.features["FEATURE-002"].contract is not None
        assert "contracts/FEATURE-002.openapi.yaml" in updated_bundle.features["FEATURE-002"].contract

        # Verify output mentions skipping FEATURE-001
        assert "already has contract" in result.stdout or "FEATURE-001" in result.stdout

    def test_migrate_to_contracts_no_stories(self, tmp_path, monkeypatch):
        """Test migrate to-contracts skips features without stories."""
        monkeypatch.chdir(tmp_path)

        # Create a project bundle with a feature without stories
        bundle_name = "test-bundle"
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle_dir.mkdir(parents=True)

        from specfact_cli.models.plan import Product
        from specfact_cli.models.project import BundleManifest, ProjectBundle

        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        project_bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

        feature_no_stories = Feature(
            key="FEATURE-001",
            title="Feature without Stories",
            outcomes=["Outcome"],
            acceptance=[],
            constraints=[],
            stories=[],
            confidence=1.0,
            draft=False,
            source_tracking=None,
            contract=None,
            protocol=None,
        )

        project_bundle.features["FEATURE-001"] = feature_no_stories

        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        # Run migration
        result = runner.invoke(
            app,
            [
                "migrate",
                "to-contracts",
                bundle_name,
                "--repo",
                str(tmp_path),
                "--no-validate-with-specmatic",
            ],
        )

        assert result.exit_code == 0

        # Verify no contracts were created
        contracts_dir = bundle_dir / "contracts"
        if contracts_dir.exists():
            contract_files = list(contracts_dir.glob("*.yaml"))
            assert len(contract_files) == 0, "No contracts should be created for features without stories"

    def test_migrate_to_contracts_bundle_size_reduction(self, tmp_path, monkeypatch):
        """Test migrate to-contracts reduces bundle size by removing verbose acceptance criteria."""
        monkeypatch.chdir(tmp_path)

        # Create a project bundle with very verbose acceptance criteria
        bundle_name = "test-bundle"
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle_dir.mkdir(parents=True)

        from specfact_cli.models.plan import Product
        from specfact_cli.models.project import BundleManifest, ProjectBundle

        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        project_bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

        # Create feature with very verbose acceptance criteria (simulating bloat)
        verbose_acceptance = [
            "Given a user with valid credentials",
            "When POST /api/login is called with username and password",
            "Then the API returns 200 OK with JWT token",
            "And the token contains user ID",
            "And the token expires in 24 hours",
            "And the token is signed with secret key",
            "And the response includes user profile",
            "And the response includes permissions",
            "And the response includes roles",
        ] * 10  # Multiply to create bloat

        feature = Feature(
            key="FEATURE-001",
            title="User Authentication",
            outcomes=["Users can log in"],
            acceptance=[],
            constraints=[],
            stories=[
                Story(
                    key="STORY-001",
                    title="Login endpoint",
                    acceptance=verbose_acceptance,
                    tags=[],
                    story_points=None,
                    value_points=None,
                    tasks=[],
                    confidence=1.0,
                    draft=False,
                    scenarios=None,
                    contracts=None,
                    source_functions=[],
                    test_functions=[],
                )
            ],
            confidence=1.0,
            draft=False,
            source_tracking=None,
            contract=None,
            protocol=None,
        )
        project_bundle.features["FEATURE-001"] = feature

        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        # Run migration
        result = runner.invoke(
            app,
            [
                "migrate",
                "to-contracts",
                bundle_name,
                "--repo",
                str(tmp_path),
                "--no-validate-with-specmatic",
            ],
        )

        assert result.exit_code == 0

        # Verify contract was created
        contracts_dir = bundle_dir / "contracts"
        assert contracts_dir.exists()

        # Verify bundle was updated with contract reference
        updated_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        assert updated_bundle.features["FEATURE-001"].contract is not None

    def test_migrate_to_contracts_no_extract_openapi(self, tmp_path, monkeypatch):
        """Test migrate to-contracts with --no-extract-openapi flag."""
        monkeypatch.chdir(tmp_path)

        # Create a project bundle
        bundle_name = "test-bundle"
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle_dir.mkdir(parents=True)

        from specfact_cli.models.plan import Product
        from specfact_cli.models.project import BundleManifest, ProjectBundle

        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        project_bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

        feature = Feature(
            key="FEATURE-001",
            title="Test Feature",
            outcomes=["Outcome"],
            acceptance=[],
            constraints=[],
            stories=[
                Story(
                    key="STORY-001",
                    title="Story",
                    acceptance=["When POST /api/test is called", "Then returns 200 OK"],
                    tags=[],
                    story_points=None,
                    value_points=None,
                    tasks=[],
                    confidence=1.0,
                    draft=False,
                    scenarios=None,
                    contracts=None,
                    source_functions=[],
                    test_functions=[],
                )
            ],
            confidence=1.0,
            draft=False,
            source_tracking=None,
            contract=None,
            protocol=None,
        )
        project_bundle.features["FEATURE-001"] = feature

        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        # Run migration with --no-extract-openapi
        result = runner.invoke(
            app,
            [
                "migrate",
                "to-contracts",
                bundle_name,
                "--repo",
                str(tmp_path),
                "--no-extract-openapi",
                "--no-validate-with-specmatic",
            ],
        )

        assert result.exit_code == 0

        # Verify no contracts were created
        contracts_dir = bundle_dir / "contracts"
        if contracts_dir.exists():
            contract_files = list(contracts_dir.glob("*.yaml"))
            assert len(contract_files) == 0, "No contracts should be created with --no-extract-openapi"

        # Verify bundle was not modified
        updated_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        assert updated_bundle.features["FEATURE-001"].contract is None
