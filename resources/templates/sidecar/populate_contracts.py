#!/usr/bin/env python3
# pyright: reportMissingImports=false, reportImplicitRelativeImport=false
"""
Populate OpenAPI contract stubs with Django URL patterns.

Reads Django URL patterns and populates existing OpenAPI contract files.

Note: This is a template file that gets copied to the sidecar workspace.
The imports work at runtime when the file is in the sidecar directory.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING, cast

import yaml


# Type stubs for template file imports
# These are template files that get copied to sidecar workspace where imports work at runtime
if TYPE_CHECKING:

    def extract_django_urls(repo_path: Path, urls_file: Path | None = None) -> list[dict[str, object]]: ...
    def extract_view_form_schema(repo_path: Path, view_module: str, view_function: str) -> dict[str, object] | None: ...


# Import from same directory (sidecar templates)
# These scripts are run directly, so we need to handle imports differently
# Add current directory to path for direct import when run as script
_script_dir = Path(__file__).parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

# These imports work at runtime when scripts are run directly from sidecar directory
# Type checker uses TYPE_CHECKING stubs above; runtime uses actual imports below
# The sidecar directory has __init__.py, making it a package, so relative imports work at runtime
try:
    # Try explicit relative imports first (preferred for type checking)
    # These work when the sidecar directory is a proper package (has __init__.py)
    from .django_form_extractor import (  # type: ignore[reportMissingImports]
        extract_view_form_schema,
    )
    from .django_url_extractor import extract_django_urls  # type: ignore[reportMissingImports]
except ImportError:
    # Fallback for when run as script (runtime path manipulation case)
    # This happens when the script is executed directly from the sidecar workspace
    # and sys.path manipulation makes absolute imports work
    from django_form_extractor import (  # type: ignore[reportMissingImports]
        extract_view_form_schema,
    )
    from django_url_extractor import (
        extract_django_urls,  # type: ignore[reportImplicitRelativeImport, reportMissingImports]
    )


def _match_url_to_feature(url_pattern: dict[str, object], feature_key: str) -> bool:
    """
    Match URL pattern to feature by operation_id or view name.

    Args:
        url_pattern: URL pattern dictionary from extractor
        feature_key: Feature key (e.g., 'FEATURE-USER-AUTHENTICATION')

    Returns:
        True if pattern matches feature
    """
    operation_id = str(url_pattern.get("operation_id", "")).lower()
    view = str(url_pattern.get("view", "")).lower()
    feature_lower = feature_key.lower().replace("feature-", "").replace("-", "_")

    # Check if operation_id or view contains feature keywords
    keywords = feature_lower.split("_")
    return any(keyword and (keyword in operation_id or keyword in view) for keyword in keywords)


def _create_openapi_operation(
    url_pattern: dict[str, object],
    repo_path: Path,
    form_schema: dict[str, object] | None = None,
) -> dict[str, object]:
    """
    Create OpenAPI operation from Django URL pattern.

    Args:
        url_pattern: URL pattern dictionary from extractor
        repo_path: Path to Django repository (for form extraction)
        form_schema: Optional pre-extracted form schema

    Returns:
        OpenAPI operation dictionary
    """
    method = str(url_pattern["method"]).lower()
    path = str(url_pattern["path"])
    operation_id = str(url_pattern["operation_id"])
    path_params = url_pattern.get("path_params", [])
    if not isinstance(path_params, list):
        path_params = []
    view_ref = url_pattern.get("view")

    operation: dict[str, object] = {
        "operationId": operation_id,
        "summary": f"{method.upper()} {path}",
        "responses": {
            "200": {"description": "Success"},
            "400": {"description": "Bad request"},
            "500": {"description": "Internal server error"},
        },
    }

    # Add path parameters
    if path_params:
        operation["parameters"] = path_params

    # Add request body for POST/PUT/PATCH
    if method in ("post", "put", "patch"):
        # Try to extract form schema from view
        schema: dict[str, object] | None = form_schema
        if schema is None and view_ref:
            # Try to extract from view function
            view_str = str(view_ref)
            if "." in view_str:
                parts = view_str.split(".")
                if len(parts) >= 2:
                    view_module = ".".join(parts[:-1])
                    view_function = parts[-1]
                    schema = extract_view_form_schema(repo_path, view_module, view_function)

        # Special case: login view doesn't use a form
        if schema is None and "login" in operation_id.lower():
            schema = {
                "type": "object",
                "properties": {
                    "username": {"type": "string", "minLength": 1},
                    "password": {"type": "string", "minLength": 1},
                },
                "required": ["username", "password"],
            }

        # Use extracted schema or default empty schema
        if schema is None:
            schema = {"type": "object", "properties": {}, "required": []}

        operation["requestBody"] = {
            "required": True,
            "content": {
                "application/x-www-form-urlencoded": {
                    "schema": schema,
                }
            },
        }

    return operation  # type: ignore[return-value]


def populate_contracts(
    contracts_dir: Path, repo_path: Path, urls_file: Path | None = None, extract_forms: bool = True
) -> dict[str, int]:
    """
    Populate OpenAPI contract stubs with Django URL patterns.

    Args:
        contracts_dir: Directory containing *.openapi.yaml files
        repo_path: Path to Django repository
        urls_file: Path to urls.py file (auto-detected if not provided)

    Returns:
        Dictionary with statistics (populated, skipped, errors)
    """
    # Extract Django URL patterns
    url_patterns = extract_django_urls(repo_path, urls_file)

    if not url_patterns:
        return {"populated": 0, "skipped": 0, "errors": 0}

    # Find all contract files
    contract_files = list(contracts_dir.glob("*.openapi.yaml"))

    stats = {"populated": 0, "skipped": 0, "errors": 0}

    for contract_file in contract_files:
        try:
            # Load contract
            with contract_file.open("r", encoding="utf-8") as f:
                contract_data = yaml.safe_load(f)  # type: ignore[assignment]
                if not isinstance(contract_data, dict):
                    contract_data = {}
                contract = cast(dict[str, object], contract_data)

            if "paths" not in contract:
                contract["paths"] = {}

            # Extract feature key from filename
            feature_key = contract_file.stem.replace(".openapi", "").upper()

            # Find matching URL patterns
            matching_patterns = [p for p in url_patterns if _match_url_to_feature(p, feature_key)]

            if not matching_patterns:
                stats["skipped"] += 1
                continue

            # Populate paths
            for pattern in matching_patterns:
                path = str(pattern["path"])
                method = str(pattern["method"]).lower()

                paths_dict = contract.get("paths", {})
                if not isinstance(paths_dict, dict):
                    paths_dict = {}
                    contract["paths"] = paths_dict
                if path not in paths_dict:
                    paths_dict[path] = {}  # type: ignore[assignment]

                # Extract form schema if enabled
                form_schema: dict[str, object] | None = None
                if extract_forms:
                    view_ref = pattern.get("view")
                    if view_ref:
                        view_str = str(view_ref)
                        if "." in view_str:
                            parts = view_str.split(".")
                            if len(parts) >= 2:
                                view_module = ".".join(parts[:-1])
                                view_function = parts[-1]
                                form_schema = extract_view_form_schema(repo_path, view_module, view_function)

                operation = _create_openapi_operation(pattern, repo_path, form_schema)  # type: ignore[arg-type]
                if isinstance(paths_dict, dict) and isinstance(paths_dict.get(path), dict):
                    paths_dict[path][method] = operation  # type: ignore[assignment, index]

            # Save updated contract
            with contract_file.open("w", encoding="utf-8") as f:
                yaml.dump(contract, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

            stats["populated"] += 1

        except Exception as e:
            print(f"Error processing {contract_file}: {e}")
            stats["errors"] += 1

    return stats


def main() -> int:
    """Main entry point for contract population."""
    parser = argparse.ArgumentParser(description="Populate OpenAPI contracts with Django URL patterns.")
    parser.add_argument("--contracts", required=True, help="Contracts directory containing *.openapi.yaml files")
    parser.add_argument("--repo", required=True, help="Path to Django repository")
    parser.add_argument("--urls", help="Path to urls.py file (auto-detected if not provided)")
    args = parser.parse_args()

    contracts_dir = Path(str(args.contracts)).resolve()  # type: ignore[arg-type]
    repo_path = Path(str(args.repo)).resolve()  # type: ignore[arg-type]
    urls_file = Path(str(args.urls)).resolve() if args.urls else None  # type: ignore[arg-type]

    # Suppress unused result warnings for argparse (these are intentional)
    _ = parser.add_argument  # type: ignore[assignment, unused-ignore]

    if not contracts_dir.exists():
        print(f"Error: Contracts directory not found: {contracts_dir}")
        return 1

    if not repo_path.exists():
        print(f"Error: Repository path not found: {repo_path}")
        return 1

    stats = populate_contracts(contracts_dir, repo_path, urls_file)

    print(f"Populated: {stats['populated']}, Skipped: {stats['skipped']}, Errors: {stats['errors']}")

    return 0 if stats["errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
