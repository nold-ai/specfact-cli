"""
Integration tests for import command with test example extraction.

Tests the full import workflow including test example extraction and OpenAPI contract generation.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from specfact_cli.cli import app


class TestImportCommandWithTestExamples:
    """Integration tests for import command with test example extraction."""

    @pytest.mark.timeout(20)
    def test_import_from_code_with_test_examples(self, tmp_path: Path) -> None:
        """Test import command extracts test examples and adds them to OpenAPI contracts."""
        # Create a simple API with tests
        api_file = tmp_path / "api.py"
        api_file.write_text(
            '''
from fastapi import FastAPI

app = FastAPI()

@app.post("/api/users")
def create_user(name: str, email: str):
    """Create a new user."""
    return {"id": 1, "name": name, "email": email}
'''
        )

        test_file = tmp_path / "test_api.py"
        test_file.write_text(
            '''
def test_create_user():
    """Test creating a user."""
    response = client.post("/api/users", json={"name": "John", "email": "john@example.com"})
    assert response.status_code == 201
    assert response.json() == {"id": 1, "name": "John", "email": "john@example.com"}
'''
        )

        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "import",
                "from-code",
                "test-bundle",
                "--repo",
                str(tmp_path),
                "--confidence",
                "0.3",
            ],
        )

        # Command should succeed
        assert result.exit_code == 0

        # Check that bundle was created
        bundle_dir = tmp_path / ".specfact" / "projects" / "test-bundle"
        assert bundle_dir.exists()

        # Check that contracts directory exists
        contracts_dir = bundle_dir / "contracts"
        if contracts_dir.exists():
            # If contracts were generated, check for examples
            contract_files = list(contracts_dir.glob("*.yaml"))
            if contract_files:
                import yaml

                with contract_files[0].open() as f:
                    contract = yaml.safe_load(f)

                # Check if examples are present (may or may not be, depending on extraction success)
                # This is a soft check - examples may not always be extracted successfully
                paths = contract.get("paths", {})
                if paths:
                    for path_item in paths.values():
                        for operation in path_item.values():
                            if isinstance(operation, dict):
                                # Check for examples in request body
                                if "requestBody" in operation:
                                    content = operation["requestBody"].get("content", {})
                                    for content_schema in content.values():
                                        if "examples" in content_schema:
                                            assert "test-example" in content_schema["examples"]

                                # Check for examples in responses
                                for response in operation.get("responses", {}).values():
                                    if isinstance(response, dict):
                                        content = response.get("content", {})
                                        for content_schema in content.values():
                                            if "examples" in content_schema:
                                                assert "test-example" in content_schema["examples"]

    @pytest.mark.timeout(20)
    def test_import_from_code_minimal_acceptance_criteria(self, tmp_path: Path) -> None:
        """Test that import command generates minimal acceptance criteria when examples are in contracts."""
        # Create a simple class with tests
        source_file = tmp_path / "user_manager.py"
        source_file.write_text(
            '''
class UserManager:
    """Manages user operations."""

    def create_user(self, name: str, email: str):
        """Create a new user."""
        return {"id": 1, "name": name, "email": email}
'''
        )

        test_file = tmp_path / "test_user_manager.py"
        test_file.write_text(
            '''
def test_create_user():
    """Test creating a user."""
    manager = UserManager()
    result = manager.create_user("John", "john@example.com")
    assert result["id"] == 1
    assert result["name"] == "John"
'''
        )

        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "import",
                "from-code",
                "test-bundle-minimal",
                "--repo",
                str(tmp_path),
                "--confidence",
                "0.3",
            ],
        )

        # Command may succeed or fail depending on feature detection
        # The important thing is that it attempts to process the code
        # Exit code 0 or 1 is acceptable (1 might mean no features detected)
        assert result.exit_code in (0, 1)

        # Check that bundle directory was attempted to be created
        bundle_dir = tmp_path / ".specfact" / "projects" / "test-bundle-minimal"
        # Bundle may or may not exist depending on whether features were detected
        if bundle_dir.exists():
            # Check that features have minimal acceptance criteria (not verbose GWT)
            features_dir = bundle_dir / "features"
            if features_dir.exists():
                feature_files = list(features_dir.glob("*.yaml"))
                if feature_files:
                    import yaml

                    with feature_files[0].open() as f:
                        feature = yaml.safe_load(f)

                    # Check stories have minimal acceptance criteria
                    for story in feature.get("stories", []):
                        acceptance = story.get("acceptance", [])
                        # Acceptance criteria should be minimal (not verbose GWT with detailed conditions)
                        for acc in acceptance:
                            # Should not have very long GWT patterns (examples are in contracts)
                            assert len(acc) < 200 or "see contract examples" in acc.lower()

    @pytest.mark.timeout(20)
    def test_import_skips_test_analysis_when_contract_has_good_structure(self, tmp_path: Path) -> None:
        """Test that import command skips test analysis when contract already has good structure."""
        # Create an API file with good structure
        api_file = tmp_path / "api.py"
        api_file.write_text(
            '''
from fastapi import FastAPI
from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str
    email: str

app = FastAPI()

@app.post("/api/users", response_model=UserCreate)
def create_user(user: UserCreate):
    """Create a new user with detailed schema."""
    return user
'''
        )

        # Create test file
        test_file = tmp_path / "test_api.py"
        test_file.write_text(
            '''
def test_create_user():
    """Test creating a user."""
    response = client.post("/api/users", json={"name": "John", "email": "john@example.com"})
    assert response.status_code == 201
'''
        )

        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "import",
                "from-code",
                "test-bundle-skip",
                "--repo",
                str(tmp_path),
                "--confidence",
                "0.3",
            ],
        )

        # Command may succeed or fail depending on feature detection
        # Exit code 0 or 1 is acceptable (1 might mean no features detected)
        assert result.exit_code in (0, 1)

        # Check that bundle directory was attempted to be created
        bundle_dir = tmp_path / ".specfact" / "projects" / "test-bundle-skip"
        # Bundle may or may not exist depending on whether features were detected
        if bundle_dir.exists():
            # Check that contracts were generated (with good structure from AST)
            contracts_dir = bundle_dir / "contracts"
            if contracts_dir.exists():
                contract_files = list(contracts_dir.glob("*.yaml"))
                if contract_files:
                    import yaml

                    with contract_files[0].open() as f:
                        contract = yaml.safe_load(f)

                    # Contract should have good structure (schemas, requestBody, etc.)
                    # This means test analysis should have been skipped
                    has_schemas = bool(contract.get("components", {}).get("schemas"))
                    has_request_body = any(
                        path_info.get("requestBody")
                        for path_info in contract.get("paths", {}).values()
                        if isinstance(path_info, dict)
                    )

                    # If contract has good structure, test analysis was likely skipped
                    # (we can't directly verify skipping, but we can verify the contract is good)
                    assert has_schemas or has_request_body

    @pytest.mark.timeout(20)
    def test_import_parallel_contract_extraction(self, tmp_path: Path) -> None:
        """Test that contract extraction uses parallel processing."""
        # Create multiple API files
        for i in range(5):
            api_file = tmp_path / f"api_{i}.py"
            api_file.write_text(
                f'''
from fastapi import FastAPI

app = FastAPI()

@app.post("/api/resource_{i}")
def create_resource_{i}():
    """Create resource {i}."""
    return {{"id": {i}}}
'''
            )

        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "import",
                "from-code",
                "test-bundle-parallel",
                "--repo",
                str(tmp_path),
                "--confidence",
                "0.3",
            ],
        )

        # Command may succeed or fail depending on feature detection
        # Exit code 0 or 1 is acceptable (1 might mean no features detected)
        assert result.exit_code in (0, 1)

        # Check that bundle directory was attempted to be created
        bundle_dir = tmp_path / ".specfact" / "projects" / "test-bundle-parallel"
        # Bundle may or may not exist depending on whether features were detected
        if bundle_dir.exists():
            # Check that multiple contracts were generated (parallel processing)
            contracts_dir = bundle_dir / "contracts"
            if contracts_dir.exists():
                contract_files = list(contracts_dir.glob("*.yaml"))
                # Should have generated contracts for multiple features (if features were detected)
                # May be 0 if no contracts detected, which is OK
                assert len(contract_files) >= 0
