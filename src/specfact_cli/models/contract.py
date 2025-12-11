"""
OpenAPI contract models for project bundles.

This module defines Pydantic models for OpenAPI contracts that are
stored in bundle-specific contracts/ directories and linked to features.

**OpenAPI Version Strategy:**
- **Default**: OpenAPI 3.0.3 for new contracts (ensures compatibility with Specmatic)
- **Validation**: Accepts both 3.0.x and 3.1.x (forward-compatible)
- **Future**: Will default to 3.1.x once Specmatic adds official support

**Current Status (December 2025):**
- Specmatic: Supports 3.0.x, 3.1.x support planned but not yet released
- We default to 3.0.3 for maximum compatibility
- Validation accepts 3.1.x for future-proofing
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require
from pydantic import BaseModel, Field


class ContractStatus(str, Enum):
    """Contract status levels."""

    DRAFT = "draft"  # Initial contract, not validated
    VALIDATED = "validated"  # Schema validated
    TESTED = "tested"  # Contract tests passing
    DEPLOYED = "deployed"  # Contract deployed to production


class ContractMetadata(BaseModel):
    """Metadata for an OpenAPI contract."""

    feature_key: str = Field(..., description="Feature key (e.g., FEATURE-001)")
    contract_file: str = Field(..., description="Contract file path relative to bundle")
    status: ContractStatus = Field(ContractStatus.DRAFT, description="Contract status")
    openapi_version: str = Field("3.0.3", description="OpenAPI specification version")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    validated_at: str | None = Field(None, description="Last validation timestamp")
    tested_at: str | None = Field(None, description="Last test execution timestamp")
    coverage: float = Field(0.0, description="Test coverage percentage (0.0-1.0)")


class ContractIndex(BaseModel):
    """Contract index entry for fast lookup."""

    feature_key: str = Field(..., description="Feature key (FEATURE-001)")
    contract_file: str = Field(..., description="Contract file path (contracts/FEATURE-001.openapi.yaml)")
    status: ContractStatus = Field(ContractStatus.DRAFT, description="Contract status")
    checksum: str | None = Field(None, description="Contract file checksum")
    endpoints_count: int = Field(0, description="Number of API endpoints")
    coverage: float = Field(0.0, description="Test coverage percentage")


@beartype
@require(lambda contract_path: isinstance(contract_path, Path), "Contract path must be Path")
@require(lambda contract_path: contract_path.exists(), "Contract file must exist")
@ensure(lambda result: isinstance(result, dict), "Must return dict")
def load_openapi_contract(contract_path: Path) -> dict[str, Any]:
    """
    Load OpenAPI contract from file.

    Args:
        contract_path: Path to OpenAPI contract file

    Returns:
        Parsed OpenAPI contract dictionary

    Raises:
        ValueError: If contract file is invalid or cannot be parsed
    """
    import yaml

    try:
        with contract_path.open(encoding="utf-8") as f:
            contract_data = yaml.safe_load(f)
            if not isinstance(contract_data, dict):
                raise ValueError(f"Contract file {contract_path} is not a valid YAML dictionary")
            return contract_data
    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse OpenAPI contract {contract_path}: {e}") from e
    except Exception as e:
        raise ValueError(f"Failed to load OpenAPI contract {contract_path}: {e}") from e


@beartype
@require(lambda contract_data: isinstance(contract_data, dict), "Contract data must be dict")
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def validate_openapi_schema(contract_data: dict[str, Any]) -> bool:
    """
    Validate OpenAPI contract schema.

    Args:
        contract_data: Parsed OpenAPI contract dictionary

    Returns:
        True if contract is valid, False otherwise

    Note:
        This performs basic validation. For full validation, use openapi-spec-validator.
    """
    # Basic validation: check required OpenAPI fields
    if "openapi" not in contract_data:
        return False
    if "info" not in contract_data:
        return False
    if "paths" not in contract_data:
        return False

    # Validate OpenAPI version
    # Accept both 3.0.x and 3.1.x for forward compatibility
    # Note: We default to 3.0.3 for generation (Specmatic compatibility)
    # but accept 3.1.x in validation for future-proofing
    # Specmatic 3.1.x support is planned but not yet released (as of Dec 2025)
    openapi_version = contract_data.get("openapi", "")
    return openapi_version.startswith(("3.0", "3.1"))


@beartype
@require(lambda contract_data: isinstance(contract_data, dict), "Contract data must be dict")
@ensure(lambda result: isinstance(result, int), "Must return int")
def count_endpoints(contract_data: dict[str, Any]) -> int:
    """
    Count API endpoints in OpenAPI contract.

    Args:
        contract_data: Parsed OpenAPI contract dictionary

    Returns:
        Number of API endpoints (paths x methods)
    """
    paths = contract_data.get("paths", {})
    endpoint_count = 0

    for _path, methods in paths.items():
        if isinstance(methods, dict):
            # Count HTTP methods (get, post, put, delete, patch, etc.)
            http_methods = ["get", "post", "put", "delete", "patch", "head", "options", "trace"]
            for method in http_methods:
                if method in methods:
                    endpoint_count += 1

    return endpoint_count
