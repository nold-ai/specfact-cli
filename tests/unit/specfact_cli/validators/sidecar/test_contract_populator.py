"""
Unit tests for contract population logic.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from specfact_cli.validators.sidecar.contract_populator import (
    load_contract,
    populate_contract,
    populate_contracts,
    save_contract,
)
from specfact_cli.validators.sidecar.frameworks.base import RouteInfo


def test_load_contract(tmp_path: Path) -> None:
    """Test loading OpenAPI contract from file."""
    contract_file = tmp_path / "contract.yaml"
    contract_data = {"openapi": "3.0.3", "paths": {}}
    with contract_file.open("w", encoding="utf-8") as f:
        yaml.dump(contract_data, f)

    result = load_contract(contract_file)
    assert result == contract_data


def test_save_contract(tmp_path: Path) -> None:
    """Test saving OpenAPI contract to file."""
    contract_file = tmp_path / "contract.yaml"
    contract_data = {"openapi": "3.0.3", "paths": {}}

    # Create file first to satisfy contract requirement
    contract_file.touch()

    save_contract(contract_file, contract_data)

    assert contract_file.exists()
    loaded = load_contract(contract_file)
    assert loaded == contract_data


def test_populate_contract(tmp_path: Path) -> None:
    """Test populating contract with routes."""
    contract_data = {"openapi": "3.0.3", "paths": {}}
    routes = [
        RouteInfo(
            path="/api/users",
            method="GET",
            operation_id="get_users",
            path_params=[],
        )
    ]
    schemas = {"GET:/api/users": {"type": "object", "properties": {}}}

    result = populate_contract(contract_data, routes, schemas)
    assert result is True
    assert "/api/users" in contract_data["paths"]
    assert "get" in contract_data["paths"]["/api/users"]


def test_populate_contracts(tmp_path: Path) -> None:
    """Test populating multiple contracts."""
    contracts_dir = tmp_path / "contracts"
    contracts_dir.mkdir()

    # Create contract file
    contract_file = contracts_dir / "FEATURE-001.yaml"
    contract_data = {"openapi": "3.0.3", "paths": {}}
    with contract_file.open("w", encoding="utf-8") as f:
        yaml.dump(contract_data, f)

    routes = [
        RouteInfo(
            path="/api/users",
            method="GET",
            operation_id="get_users",
            path_params=[],
        )
    ]
    schemas = {"GET:/api/users": {"type": "object", "properties": {}}}

    result = populate_contracts(contracts_dir, routes, schemas)
    assert result == 1


def test_populate_contracts_no_contracts(tmp_path: Path) -> None:
    """Test populating contracts when no contracts exist."""
    contracts_dir = tmp_path / "contracts"
    contracts_dir.mkdir()

    routes: list[RouteInfo] = []
    schemas: dict[str, dict] = {}

    result = populate_contracts(contracts_dir, routes, schemas)
    assert result == 0
