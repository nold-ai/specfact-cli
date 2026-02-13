"""
Unit tests for harness generation logic.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from specfact_cli.validators.sidecar.harness_generator import (
    extract_operations,
    generate_harness,
    render_harness,
)


def test_extract_operations() -> None:
    """Test extracting operations from OpenAPI contract."""
    contract_data = {
        "openapi": "3.0.3",
        "paths": {
            "/api/users": {
                "get": {
                    "operationId": "get_users",
                    "responses": {"200": {"description": "Success"}},
                }
            }
        },
    }

    operations = extract_operations(contract_data)
    assert len(operations) == 1
    assert operations[0]["operation_id"] == "get_users"
    assert operations[0]["path"] == "/api/users"
    assert operations[0]["method"] == "GET"


def test_render_harness() -> None:
    """Test rendering harness Python code."""
    operations = [
        {
            "operation_id": "get_users",
            "path": "/api/users",
            "method": "GET",
            "request_schema": {},
            "response_schema": {},
        }
    ]

    harness_code = render_harness(operations)
    assert "def harness_get_users" in harness_code
    assert "@beartype" in harness_code
    assert "@require" in harness_code
    assert "@ensure" in harness_code


def test_generate_harness(tmp_path: Path) -> None:
    """Test generating harness file."""
    contracts_dir = tmp_path / "contracts"
    contracts_dir.mkdir()
    harness_path = tmp_path / "harness_contracts.py"

    # Create contract file
    contract_file = contracts_dir / "FEATURE-001.yaml"
    contract_data = {
        "openapi": "3.0.3",
        "paths": {
            "/api/users": {
                "get": {
                    "operationId": "get_users",
                    "responses": {"200": {"description": "Success"}},
                }
            }
        },
    }
    with contract_file.open("w", encoding="utf-8") as f:
        yaml.dump(contract_data, f)

    result = generate_harness(contracts_dir, harness_path)
    assert result is True
    assert harness_path.exists()
    content = harness_path.read_text()
    assert "def harness_get_users" in content


def test_generate_harness_no_contracts(tmp_path: Path) -> None:
    """Test generating harness when no contracts exist."""
    contracts_dir = tmp_path / "contracts"
    contracts_dir.mkdir()
    harness_path = tmp_path / "harness_contracts.py"

    result = generate_harness(contracts_dir, harness_path)
    assert result is False


def test_extract_operations_includes_response_examples() -> None:
    """Test that extract_operations extracts response examples for constraint inference."""
    contract_data = {
        "openapi": "3.0.3",
        "paths": {
            "/api/users/{id}": {
                "get": {
                    "operationId": "get_user",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {"id": {"type": "integer"}},
                                        "example": {"id": 1, "name": "Alice"},
                                    }
                                }
                            },
                        }
                    },
                }
            }
        },
    }

    operations = extract_operations(contract_data)
    assert len(operations) == 1
    assert "response_examples" in operations[0]
    assert len(operations[0]["response_examples"]) >= 1
    assert operations[0]["response_examples"][0]["id"] == 1


def test_render_harness_business_logic_preconditions() -> None:
    """Test that harness includes business logic preconditions for path params."""
    operations = [
        {
            "operation_id": "get_user",
            "path": "/api/users/{id}",
            "method": "GET",
            "parameters": [
                {
                    "name": "id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "integer"},
                }
            ],
            "request_schema": None,
            "response_schema": {},
            "expected_status_codes": [200],
            "response_examples": [],
        }
    ]

    harness_code = render_harness(operations)
    assert "id >= 1" in harness_code or "id must be >= 1" in harness_code


def test_render_harness_enum_preconditions() -> None:
    """Test that harness includes enum preconditions from schema."""
    operations = [
        {
            "operation_id": "get_status",
            "path": "/api/status/{status}",
            "method": "GET",
            "parameters": [
                {
                    "name": "status",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string", "enum": ["active", "inactive"]},
                }
            ],
            "request_schema": None,
            "response_schema": {},
            "expected_status_codes": [200],
            "response_examples": [],
        }
    ]

    harness_code = render_harness(operations)
    assert "active" in harness_code and "inactive" in harness_code


def test_render_harness_id_postcondition() -> None:
    """Test that harness includes business rule postcondition for id >= 1."""
    operations = [
        {
            "operation_id": "create_user",
            "path": "/api/users",
            "method": "POST",
            "parameters": [],
            "request_schema": None,
            "response_schema": {
                "type": "object",
                "properties": {"id": {"type": "integer"}, "name": {"type": "string"}},
                "required": ["id", "name"],
            },
            "expected_status_codes": [200, 201],
            "response_examples": [],
        }
    ]

    harness_code = render_harness(operations)
    assert "id" in harness_code and ">= 1" in harness_code
