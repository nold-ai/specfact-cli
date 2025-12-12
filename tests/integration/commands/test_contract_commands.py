"""Integration tests for contract commands."""

import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.models.plan import Feature, Product, Story
from specfact_cli.models.project import BundleManifest, ProjectBundle
from specfact_cli.utils.bundle_loader import save_project_bundle


runner = CliRunner()


@pytest.fixture
def sample_bundle_with_contract(tmp_path: Path, monkeypatch) -> tuple[Path, str]:
    """Create a sample project bundle with contract for testing."""
    monkeypatch.chdir(tmp_path)

    # Create .specfact structure
    projects_dir = tmp_path / ".specfact" / "projects"
    projects_dir.mkdir(parents=True)

    bundle_name = "test-bundle"
    bundle_dir = projects_dir / bundle_name
    bundle_dir.mkdir()

    # Create ProjectBundle
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


class TestContractInit:
    """Test suite for contract init command."""

    def test_init_contract(self, sample_bundle_with_contract: tuple[Path, str]) -> None:
        """Test initializing a new OpenAPI contract."""
        repo_path, bundle_name = sample_bundle_with_contract
        os.environ["TEST_MODE"] = "true"

        result = runner.invoke(
            app,
            [
                "contract",
                "init",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--feature",
                "FEATURE-001",
                "--title",
                "Test API",
                "--version",
                "1.0.0",
                "--no-interactive",
            ],
        )

        assert result.exit_code == 0

        # Verify contract file created
        bundle_dir = repo_path / ".specfact" / "projects" / bundle_name
        contract_file = bundle_dir / "contracts" / "FEATURE-001.openapi.yaml"
        assert contract_file.exists()

        # Verify contract content
        import yaml

        contract_data = yaml.safe_load(contract_file.read_text())
        assert contract_data["openapi"] == "3.0.3"
        assert contract_data["info"]["title"] == "Test API"
        assert contract_data["info"]["version"] == "1.0.0"


class TestContractValidate:
    """Test suite for contract validate command."""

    def test_validate_valid_contract(self, sample_bundle_with_contract: tuple[Path, str]) -> None:
        """Test validating a valid OpenAPI contract."""
        repo_path, bundle_name = sample_bundle_with_contract
        os.environ["TEST_MODE"] = "true"

        # First create a contract
        bundle_dir = repo_path / ".specfact" / "projects" / bundle_name
        contracts_dir = bundle_dir / "contracts"
        contracts_dir.mkdir(exist_ok=True)

        import yaml

        contract_data = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "get": {
                        "responses": {
                            "200": {
                                "description": "Success",
                            }
                        }
                    }
                }
            },
        }
        contract_file = contracts_dir / "FEATURE-001.openapi.yaml"
        contract_file.write_text(yaml.dump(contract_data))

        # Validate (use --feature instead of --contract)
        result = runner.invoke(
            app,
            [
                "contract",
                "validate",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--feature",
                "FEATURE-001",
                "--no-interactive",
            ],
        )

        assert result.exit_code == 0
        assert (
            "valid" in result.stdout.lower()
            or "success" in result.stdout.lower()
            or "validated" in result.stdout.lower()
        )

    def test_validate_invalid_contract(self, sample_bundle_with_contract: tuple[Path, str]) -> None:
        """Test validating an invalid OpenAPI contract."""
        repo_path, bundle_name = sample_bundle_with_contract
        os.environ["TEST_MODE"] = "true"

        # Create invalid contract
        bundle_dir = repo_path / ".specfact" / "projects" / bundle_name
        contracts_dir = bundle_dir / "contracts"
        contracts_dir.mkdir(exist_ok=True)

        contract_file = contracts_dir / "FEATURE-001.openapi.yaml"
        contract_file.write_text("invalid: yaml: content")

        # Validate
        result = runner.invoke(
            app,
            [
                "contract",
                "validate",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--contract",
                "contracts/FEATURE-001.openapi.yaml",
                "--no-interactive",
            ],
        )

        # Should fail or report error
        assert result.exit_code != 0 or "error" in result.stdout.lower() or "invalid" in result.stdout.lower()


class TestContractCoverage:
    """Test suite for contract coverage command."""

    def test_coverage_report(self, sample_bundle_with_contract: tuple[Path, str]) -> None:
        """Test generating contract coverage report."""
        repo_path, bundle_name = sample_bundle_with_contract
        os.environ["TEST_MODE"] = "true"

        # Create a contract
        bundle_dir = repo_path / ".specfact" / "projects" / bundle_name
        contracts_dir = bundle_dir / "contracts"
        contracts_dir.mkdir(exist_ok=True)

        import yaml

        contract_data = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "get": {"responses": {"200": {"description": "Success"}}},
                    "post": {"responses": {"201": {"description": "Created"}}},
                }
            },
        }
        contract_file = contracts_dir / "FEATURE-001.openapi.yaml"
        contract_file.write_text(yaml.dump(contract_data))

        # Get coverage
        result = runner.invoke(
            app,
            [
                "contract",
                "coverage",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--no-interactive",
            ],
        )

        assert result.exit_code == 0
        assert "coverage" in result.stdout.lower() or "contract" in result.stdout.lower()
