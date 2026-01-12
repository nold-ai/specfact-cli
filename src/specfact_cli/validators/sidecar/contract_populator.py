"""
Contract population logic for sidecar validation.

This module populates OpenAPI contracts with framework-extracted routes and schemas.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from beartype import beartype
from icontract import ensure, require

from specfact_cli.validators.sidecar.frameworks.base import RouteInfo


@beartype
@require(lambda contracts_dir: contracts_dir.exists(), "Contracts directory must exist")
@require(lambda routes: isinstance(routes, list), "Routes must be a list")
@ensure(lambda result: isinstance(result, int), "Must return int")
def populate_contracts(contracts_dir: Path, routes: list[RouteInfo], schemas: dict[str, dict[str, Any]]) -> int:
    """
    Populate OpenAPI contracts with framework-extracted routes and schemas.

    Args:
        contracts_dir: Directory containing OpenAPI contract files
        routes: List of extracted routes
        schemas: Dictionary mapping route identifiers to schema dictionaries

    Returns:
        Number of contracts populated
    """
    contract_files = list(contracts_dir.glob("*.yaml")) + list(contracts_dir.glob("*.yml"))
    if not contract_files:
        return 0

    populated_count = 0
    total_paths = 0

    for contract_file in contract_files:
        try:
            contract_data = load_contract(contract_file)
            if populate_contract(contract_data, routes, schemas):
                save_contract(contract_file, contract_data)
                populated_count += 1
            paths_after = len(contract_data.get("paths", {}))
            # Count total paths in contract (whether newly added or already existed)
            total_paths = max(total_paths, paths_after)
        except Exception:
            # Skip contracts that can't be processed
            continue

    # Return total number of paths in contracts (gives better indication of what was populated)
    # If no paths found, return number of contracts modified as fallback
    return total_paths if total_paths > 0 else populated_count


@beartype
@require(lambda contract_path: contract_path.exists(), "Contract file must exist")
@ensure(lambda result: isinstance(result, dict), "Must return dict")
def load_contract(contract_path: Path) -> dict[str, Any]:
    """
    Load OpenAPI contract from file.

    Args:
        contract_path: Path to contract file

    Returns:
        Contract data dictionary
    """
    with contract_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@beartype
@require(lambda contract_path: contract_path.exists(), "Contract file must exist")
@require(lambda contract_data: isinstance(contract_data, dict), "Contract data must be dict")
def save_contract(contract_path: Path, contract_data: dict[str, Any]) -> None:
    """
    Save OpenAPI contract to file.

    Args:
        contract_path: Path to contract file
        contract_data: Contract data dictionary
    """
    with contract_path.open("w", encoding="utf-8") as f:
        yaml.dump(contract_data, f, default_flow_style=False, sort_keys=False)


@beartype
@require(lambda contract_data: isinstance(contract_data, dict), "Contract data must be dict")
@require(lambda routes: isinstance(routes, list), "Routes must be a list")
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def populate_contract(
    contract_data: dict[str, Any], routes: list[RouteInfo], schemas: dict[str, dict[str, Any]]
) -> bool:
    """
    Populate a single contract with routes and schemas.

    Args:
        contract_data: Contract data dictionary (modified in place)
        routes: List of extracted routes
        schemas: Dictionary mapping route identifiers to schema dictionaries

    Returns:
        True if contract was modified
    """
    if "paths" not in contract_data:
        contract_data["paths"] = {}

    modified = False

    for route in routes:
        route_id = f"{route.method}:{route.path}"
        # Add route to paths if not already present
        if route.path not in contract_data["paths"]:
            contract_data["paths"][route.path] = {}

        method_lower = route.method.lower()
        if method_lower not in contract_data["paths"][route.path]:
            operation = {
                "operationId": route.operation_id,
                "summary": f"{route.method} {route.path}",
                "responses": {
                    "200": {"description": "Success"},
                    "400": {"description": "Bad request"},
                    "500": {"description": "Internal server error"},
                },
            }

            if route.path_params:
                operation["parameters"] = route.path_params

            # Add requestBody only if schema is available for POST/PUT/PATCH methods
            if route.method.upper() in ("POST", "PUT", "PATCH"):
                schema = schemas.get(route_id, {})
                if schema:
                    operation["requestBody"] = {
                        "content": {
                            "application/json": {
                                "schema": schema,
                            }
                        }
                    }

            contract_data["paths"][route.path][method_lower] = operation
            modified = True

    return modified
