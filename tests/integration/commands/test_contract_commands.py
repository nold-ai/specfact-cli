"""Integration tests for contract commands."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

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

        # Verify contract index in manifest
        from specfact_cli.utils.bundle_loader import load_project_bundle

        bundle = load_project_bundle(bundle_dir)
        contract_indices = [c for c in bundle.manifest.contracts if c.feature_key == "FEATURE-001"]
        assert len(contract_indices) > 0
        assert contract_indices[0].contract_file == "contracts/FEATURE-001.openapi.yaml"


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


class TestContractServe:
    """Test suite for contract serve command."""

    def test_serve_contract_feature_not_found(self, sample_bundle_with_contract: tuple[Path, str]) -> None:
        """Test serve command with non-existent feature."""
        repo_path, bundle_name = sample_bundle_with_contract
        os.environ["TEST_MODE"] = "true"

        result = runner.invoke(
            app,
            [
                "contract",
                "serve",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--feature",
                "FEATURE-999",
                "--no-interactive",
            ],
        )

        assert result.exit_code != 0
        assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()

    def test_serve_contract_no_contract(self, sample_bundle_with_contract: tuple[Path, str]) -> None:
        """Test serve command when feature has no contract."""
        repo_path, bundle_name = sample_bundle_with_contract
        os.environ["TEST_MODE"] = "true"

        # Remove contract from feature
        from specfact_cli.utils.bundle_loader import load_project_bundle, save_project_bundle
        from specfact_cli.utils.structure import SpecFactStructure

        bundle_dir = SpecFactStructure.project_dir(base_path=repo_path, bundle_name=bundle_name)
        bundle = load_project_bundle(bundle_dir)
        bundle.features["FEATURE-001"].contract = None
        save_project_bundle(bundle, bundle_dir)

        result = runner.invoke(
            app,
            [
                "contract",
                "serve",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--feature",
                "FEATURE-001",
                "--no-interactive",
            ],
        )

        assert result.exit_code != 0
        assert "no contract" in result.stdout.lower() or "error" in result.stdout.lower()


class TestContractTest:
    """Test suite for contract test command."""

    def test_test_contract_feature_not_found(self, sample_bundle_with_contract: tuple[Path, str]) -> None:
        """Test test command with non-existent feature."""
        repo_path, bundle_name = sample_bundle_with_contract
        os.environ["TEST_MODE"] = "true"

        result = runner.invoke(
            app,
            [
                "contract",
                "test",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--feature",
                "FEATURE-999",
                "--no-interactive",
            ],
        )

        assert result.exit_code != 0
        assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()

    def test_test_contract_no_contract(self, sample_bundle_with_contract: tuple[Path, str]) -> None:
        """Test test command when feature has no contract."""
        repo_path, bundle_name = sample_bundle_with_contract
        os.environ["TEST_MODE"] = "true"

        # Remove contract from feature
        from specfact_cli.utils.bundle_loader import load_project_bundle, save_project_bundle
        from specfact_cli.utils.structure import SpecFactStructure

        bundle_dir = SpecFactStructure.project_dir(base_path=repo_path, bundle_name=bundle_name)
        bundle = load_project_bundle(bundle_dir)
        bundle.features["FEATURE-001"].contract = None
        save_project_bundle(bundle, bundle_dir)

        result = runner.invoke(
            app,
            [
                "contract",
                "test",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--feature",
                "FEATURE-001",
                "--no-interactive",
            ],
        )

        assert result.exit_code != 0
        assert "no contract" in result.stdout.lower() or "error" in result.stdout.lower()


class TestContractVerify:
    """Test suite for contract verify command."""

    def test_verify_contract_feature_not_found(self, sample_bundle_with_contract: tuple[Path, str]) -> None:
        """Test verify command with non-existent feature."""
        repo_path, bundle_name = sample_bundle_with_contract
        os.environ["TEST_MODE"] = "true"

        result = runner.invoke(
            app,
            [
                "contract",
                "verify",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--feature",
                "FEATURE-999",
                "--skip-mock",
                "--no-interactive",
            ],
        )

        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()

    def test_verify_contract_no_contract(self, sample_bundle_with_contract: tuple[Path, str]) -> None:
        """Test verify command when feature has no contract."""
        repo_path, bundle_name = sample_bundle_with_contract
        os.environ["TEST_MODE"] = "true"

        # Remove contract from feature
        from specfact_cli.utils.bundle_loader import load_project_bundle, save_project_bundle
        from specfact_cli.utils.structure import SpecFactStructure

        bundle_dir = SpecFactStructure.project_dir(base_path=repo_path, bundle_name=bundle_name)
        bundle = load_project_bundle(bundle_dir)
        bundle.features["FEATURE-001"].contract = None
        save_project_bundle(bundle, bundle_dir)

        result = runner.invoke(
            app,
            [
                "contract",
                "verify",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--feature",
                "FEATURE-001",
                "--skip-mock",
                "--no-interactive",
            ],
        )

        assert result.exit_code == 1
        assert "no contract" in result.stdout.lower() or "not found" in result.stdout.lower()

    @patch("specfact_cli.integrations.specmatic.check_specmatic_available")
    @patch("specfact_cli.integrations.specmatic.generate_specmatic_examples")
    def test_verify_contract_skip_mock(
        self,
        mock_generate_examples: MagicMock,
        mock_check_specmatic: MagicMock,
        sample_bundle_with_contract: tuple[Path, str],
    ) -> None:
        """Test verify command with --skip-mock (validation only)."""
        mock_check_specmatic.return_value = (True, None)  # Mock Specmatic as available

        # Mock example generation to return a directory
        async def mock_generate(*args, **kwargs):
            return Path("/tmp/mock-examples")

        mock_generate_examples.side_effect = mock_generate
        repo_path, bundle_name = sample_bundle_with_contract
        os.environ["TEST_MODE"] = "true"

        # Create a contract for FEATURE-001
        bundle_dir = repo_path / ".specfact" / "projects" / bundle_name
        contract_path = bundle_dir / "contracts" / "FEATURE-001.openapi.yaml"
        contract_path.parent.mkdir(parents=True, exist_ok=True)
        contract_path.write_text(
            """openapi: 3.0.3
info:
  title: Test API
  version: 1.0.0
paths:
  /test:
    get:
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: object
"""
        )

        # Update bundle manifest to include contract
        from specfact_cli.utils.bundle_loader import load_project_bundle, save_project_bundle

        bundle = load_project_bundle(bundle_dir)
        if "FEATURE-001" in bundle.features:
            bundle.features["FEATURE-001"].contract = "contracts/FEATURE-001.openapi.yaml"
            save_project_bundle(bundle, bundle_dir)

        result = runner.invoke(
            app,
            [
                "contract",
                "verify",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--feature",
                "FEATURE-001",
                "--skip-mock",
                "--no-interactive",
            ],
        )

        assert result.exit_code == 0
        assert "Step 1: Validating contracts" in result.stdout
        assert "Step 2: Generating examples" in result.stdout
        assert "Skipped" in result.stdout or "skip-mock" in result.stdout.lower()
        assert "Contract verification complete" in result.stdout

    @patch("specfact_cli.integrations.specmatic.check_specmatic_available")
    @patch("specfact_cli.integrations.specmatic.generate_specmatic_examples")
    def test_verify_contract_all_contracts(
        self,
        mock_generate_examples: MagicMock,
        mock_check_specmatic: MagicMock,
        sample_bundle_with_contract: tuple[Path, str],
    ) -> None:
        """Test verify command for all contracts in bundle."""
        mock_check_specmatic.return_value = (True, None)  # Mock Specmatic as available

        # Mock example generation to return a directory
        async def mock_generate(*args, **kwargs):
            return Path("/tmp/mock-examples")

        mock_generate_examples.side_effect = mock_generate
        repo_path, bundle_name = sample_bundle_with_contract
        os.environ["TEST_MODE"] = "true"

        # Create contracts for multiple features
        bundle_dir = repo_path / ".specfact" / "projects" / bundle_name
        contracts_dir = bundle_dir / "contracts"
        contracts_dir.mkdir(parents=True, exist_ok=True)

        contract1 = contracts_dir / "FEATURE-001.openapi.yaml"
        contract1.write_text(
            """openapi: 3.0.3
info:
  title: Test API 1
  version: 1.0.0
paths:
  /test1:
    get:
      responses:
        '200':
          description: Success
"""
        )

        # Update bundle manifest
        from specfact_cli.utils.bundle_loader import load_project_bundle, save_project_bundle

        bundle = load_project_bundle(bundle_dir)
        if "FEATURE-001" in bundle.features:
            bundle.features["FEATURE-001"].contract = "contracts/FEATURE-001.openapi.yaml"
        save_project_bundle(bundle, bundle_dir)

        result = runner.invoke(
            app,
            [
                "contract",
                "verify",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--skip-mock",
                "--no-interactive",
            ],
        )

        assert result.exit_code == 0
        assert "Step 1: Validating contracts" in result.stdout
        assert "FEATURE-001" in result.stdout
        assert "Contract verification complete" in result.stdout
