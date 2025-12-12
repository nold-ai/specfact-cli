"""Integration tests for SDD contract tracking integration."""

import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.models.plan import Feature, Product, Story
from specfact_cli.models.project import BundleManifest, ProjectBundle
from specfact_cli.models.sdd import SDDManifest
from specfact_cli.utils.bundle_loader import load_project_bundle, save_project_bundle


runner = CliRunner()


@pytest.fixture
def sample_bundle_with_contract(tmp_path: Path, monkeypatch) -> tuple[Path, str]:
    """Create a sample project bundle with OpenAPI contract for SDD testing."""
    monkeypatch.chdir(tmp_path)

    # Create .specfact structure
    projects_dir = tmp_path / ".specfact" / "projects"
    projects_dir.mkdir(parents=True)

    bundle_name = "test-bundle"
    bundle_dir = projects_dir / bundle_name
    bundle_dir.mkdir()

    # Create contracts directory
    contracts_dir = bundle_dir / "contracts"
    contracts_dir.mkdir()

    # Create OpenAPI contract
    import yaml

    contract_data = {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0", "description": "Test API contract"},
        "paths": {
            "/users": {
                "get": {
                    "summary": "Get users",
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"type": "object"},
                                    }
                                }
                            },
                        }
                    },
                },
                "post": {
                    "summary": "Create user",
                    "responses": {
                        "201": {
                            "description": "Created",
                        }
                    },
                },
            }
        },
    }
    contract_file = contracts_dir / "FEATURE-001.openapi.yaml"
    contract_file.write_text(yaml.dump(contract_data))

    # Create ProjectBundle with contract reference
    manifest = BundleManifest(schema_metadata=None, project_metadata=None)
    product = Product(themes=["Testing"])
    bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

    feature = Feature(
        key="FEATURE-001",
        title="Test Feature",
        outcomes=["Test outcome"],
        stories=[
            Story(
                key="STORY-001",
                title="Test Story",
                acceptance=["Test acceptance"],
                story_points=None,
                value_points=None,
                scenarios=None,
                contracts=None,
            )
        ],
        source_tracking=None,
        contract="contracts/FEATURE-001.openapi.yaml",
        protocol=None,
    )
    bundle.add_feature(feature)

    save_project_bundle(bundle, bundle_dir, atomic=True)

    return tmp_path, bundle_name


class TestSDDContractTracking:
    """Test suite for SDD contract tracking integration."""

    def test_plan_harden_includes_contracts(
        self, sample_bundle_with_contract: tuple[Path, str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that plan harden includes OpenAPI contracts in SDD manifest."""
        repo_path, bundle_name = sample_bundle_with_contract
        os.environ["TEST_MODE"] = "true"

        # Change to repo directory (plan harden uses current directory)
        monkeypatch.chdir(repo_path)

        # Run plan harden
        result = runner.invoke(
            app,
            [
                "plan",
                "harden",
                bundle_name,
                "--no-interactive",
            ],
        )

        assert result.exit_code == 0

        # Load SDD manifest
        from specfact_cli.utils.sdd_discovery import find_sdd_for_bundle

        sdd_path = find_sdd_for_bundle(bundle_name, repo_path)
        assert sdd_path is not None

        import yaml

        sdd_data = yaml.safe_load(sdd_path.read_text())
        sdd = SDDManifest.model_validate(sdd_data)

        # Verify OpenAPI contracts are tracked
        assert hasattr(sdd.how, "openapi_contracts")
        assert len(sdd.how.openapi_contracts) > 0

        # Verify contract reference
        contract_ref = sdd.how.openapi_contracts[0]
        assert contract_ref.feature_key == "FEATURE-001"
        assert contract_ref.contract_file == "contracts/FEATURE-001.openapi.yaml"
        assert contract_ref.endpoints_count == 2  # GET and POST
        # Contract should be validated if schema is valid
        assert contract_ref.status == "validated"

    def test_enforce_sdd_validates_contract_coverage(
        self, sample_bundle_with_contract: tuple[Path, str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that enforce sdd validates OpenAPI contract coverage."""
        repo_path, bundle_name = sample_bundle_with_contract
        os.environ["TEST_MODE"] = "true"

        # Change to repo directory (plan harden uses current directory)
        monkeypatch.chdir(repo_path)

        # First create SDD manifest
        runner.invoke(
            app,
            [
                "plan",
                "harden",
                bundle_name,
                "--no-interactive",
            ],
        )

        # Run enforce sdd (bundle is an argument, not --bundle option, and uses current directory)
        result = runner.invoke(
            app,
            [
                "enforce",
                "sdd",
                bundle_name,  # Bundle is a positional argument
                "--no-interactive",
            ],
        )

        assert result.exit_code == 0

        # Verify contract coverage is reported
        assert "OpenAPI" in result.stdout or "contract" in result.stdout.lower() or "coverage" in result.stdout.lower()

    def test_contract_coverage_metrics(
        self, sample_bundle_with_contract: tuple[Path, str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test contract coverage metrics calculation."""
        repo_path, bundle_name = sample_bundle_with_contract
        os.environ["TEST_MODE"] = "true"

        # Change to repo directory (plan harden uses current directory)
        monkeypatch.chdir(repo_path)

        # Create SDD manifest
        runner.invoke(
            app,
            [
                "plan",
                "harden",
                bundle_name,
                "--no-interactive",
            ],
        )

        # Load bundle and SDD
        bundle_dir = repo_path / ".specfact" / "projects" / bundle_name
        bundle = load_project_bundle(bundle_dir, validate_hashes=False)

        from specfact_cli.utils.sdd_discovery import find_sdd_for_bundle

        sdd_path = find_sdd_for_bundle(bundle_name, repo_path)
        assert sdd_path is not None

        import yaml

        sdd_data = yaml.safe_load(sdd_path.read_text())
        sdd = SDDManifest.model_validate(sdd_data)

        # Calculate coverage
        from specfact_cli.commands.plan import _convert_project_bundle_to_plan_bundle
        from specfact_cli.validators.contract_validator import calculate_contract_density

        # Convert ProjectBundle to PlanBundle for compatibility
        plan_bundle = _convert_project_bundle_to_plan_bundle(bundle)
        metrics = calculate_contract_density(sdd, plan_bundle)

        # Verify OpenAPI coverage metrics
        assert hasattr(metrics, "openapi_coverage_percent")
        assert hasattr(metrics, "features_with_openapi")
        assert hasattr(metrics, "total_openapi_contracts")
        assert metrics.features_with_openapi >= 0
        assert metrics.total_openapi_contracts >= 0
