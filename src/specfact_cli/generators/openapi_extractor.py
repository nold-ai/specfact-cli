"""
OpenAPI contract extractor.

This module provides utilities for extracting OpenAPI 3.0.3 contracts from
verbose acceptance criteria or existing code using AST analysis.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

import yaml
from beartype import beartype
from icontract import ensure, require

from specfact_cli.integrations.specmatic import SpecValidationResult, validate_spec_with_specmatic
from specfact_cli.models.plan import Feature


class OpenAPIExtractor:
    """Extractor for generating OpenAPI contracts from features."""

    def __init__(self, repo_path: Path) -> None:
        """
        Initialize extractor with repository path.

        Args:
            repo_path: Path to repository root
        """
        self.repo_path = repo_path.resolve()

    @beartype
    @require(lambda self, feature: isinstance(feature, Feature), "Feature must be Feature instance")
    @ensure(lambda self, feature, result: isinstance(result, dict), "Must return OpenAPI dict")
    def extract_openapi_from_verbose(self, feature: Feature) -> dict[str, Any]:
        """
        Convert verbose acceptance criteria to OpenAPI contract.

        Args:
            feature: Feature with verbose acceptance criteria

        Returns:
            OpenAPI 3.0.3 specification as dictionary
        """
        # Start with basic OpenAPI structure
        openapi_spec: dict[str, Any] = {
            "openapi": "3.0.3",
            "info": {
                "title": feature.title,
                "version": "1.0.0",
                "description": f"API contract for {feature.title}",
            },
            "paths": {},
            "components": {"schemas": {}},
        }

        # Extract API endpoints from acceptance criteria
        for story in feature.stories:
            for acceptance in story.acceptance:
                # Try to extract HTTP method and path from acceptance criteria
                # Patterns like "POST /api/login", "GET /api/users", etc.
                method_path_match = re.search(
                    r"(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+(/[\w/-]+)", acceptance, re.IGNORECASE
                )
                if method_path_match:
                    method = method_path_match.group(1).upper()
                    path = method_path_match.group(2)

                    if path not in openapi_spec["paths"]:
                        openapi_spec["paths"][path] = {}

                    # Create operation
                    operation_id = f"{method.lower()}_{path.replace('/', '_').replace('-', '_').strip('_')}"
                    operation: dict[str, Any] = {
                        "operationId": operation_id,
                        "summary": story.title,
                        "description": acceptance,
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {},
                                        }
                                    }
                                },
                            }
                        },
                    }

                    # Add request body for POST/PUT/PATCH
                    if method in ("POST", "PUT", "PATCH"):
                        operation["requestBody"] = {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {},
                                    }
                                }
                            },
                        }

                    openapi_spec["paths"][path][method.lower()] = operation

        return openapi_spec

    @beartype
    @require(lambda self, repo_path: isinstance(repo_path, Path), "Repository path must be Path")
    @require(lambda self, feature: isinstance(feature, Feature), "Feature must be Feature instance")
    @ensure(lambda self, feature, result: isinstance(result, dict), "Must return OpenAPI dict")
    def extract_openapi_from_code(self, repo_path: Path, feature: Feature) -> dict[str, Any]:
        """
        Extract OpenAPI contract from existing code using AST.

        Args:
            repo_path: Path to repository
            feature: Feature to extract contract for

        Returns:
            OpenAPI 3.0.3 specification as dictionary
        """
        # Start with basic OpenAPI structure
        openapi_spec: dict[str, Any] = {
            "openapi": "3.0.3",
            "info": {
                "title": feature.title,
                "version": "1.0.0",
                "description": f"API contract extracted from code for {feature.title}",
            },
            "paths": {},
            "components": {"schemas": {}},
        }

        # Use source tracking to find implementation files
        if feature.source_tracking:
            for impl_file in feature.source_tracking.implementation_files:
                file_path = repo_path / impl_file
                if file_path.exists() and file_path.suffix == ".py":
                    self._extract_endpoints_from_file(file_path, openapi_spec)

        return openapi_spec

    def _extract_endpoints_from_file(self, file_path: Path, openapi_spec: dict[str, Any]) -> None:
        """
        Extract API endpoints from a Python file using AST.

        Args:
            file_path: Path to Python file
            openapi_spec: OpenAPI spec dictionary to update
        """
        try:
            with file_path.open(encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(file_path))

            # Look for FastAPI/Flask/Django route decorators
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check for decorators that indicate HTTP routes
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                            # FastAPI: @app.get("/path")
                            # Flask: @app.route("/path", methods=["GET"])
                            if decorator.func.attr in ("get", "post", "put", "delete", "patch", "head", "options"):
                                method = decorator.func.attr.upper()
                                # Extract path from first argument
                                if decorator.args:
                                    path_arg = decorator.args[0]
                                    if isinstance(path_arg, ast.Constant):
                                        path = path_arg.value
                                        if isinstance(path, str):
                                            self._add_operation(openapi_spec, path, method, node)
                        elif isinstance(decorator, ast.Attribute) and decorator.attr == "route":
                            # Flask: @app.route("/path")
                            # Would need to check parent Call node for path
                            pass

        except (SyntaxError, UnicodeDecodeError):
            # Skip files with syntax errors
            pass

    def _add_operation(self, openapi_spec: dict[str, Any], path: str, method: str, func_node: ast.FunctionDef) -> None:
        """
        Add operation to OpenAPI spec.

        Args:
            openapi_spec: OpenAPI spec dictionary
            path: API path
            method: HTTP method
            func_node: Function AST node
        """
        if path not in openapi_spec["paths"]:
            openapi_spec["paths"][path] = {}

        operation_id = func_node.name
        operation: dict[str, Any] = {
            "operationId": operation_id,
            "summary": func_node.name.replace("_", " ").title(),
            "description": ast.get_docstring(func_node) or "",
            "responses": {
                "200": {
                    "description": "Success",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                            }
                        }
                    },
                }
            },
        }

        # Infer request body from function parameters
        if method in ("POST", "PUT", "PATCH") and func_node.args.args:
            operation["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {},
                        }
                    }
                },
            }

        openapi_spec["paths"][path][method.lower()] = operation

    @beartype
    @require(lambda self, contract_path: isinstance(contract_path, Path), "Contract path must be Path")
    @ensure(
        lambda self, contract_path, result: isinstance(result, SpecValidationResult), "Must return SpecValidationResult"
    )
    async def validate_with_specmatic(self, contract_path: Path) -> SpecValidationResult:
        """
        Validate OpenAPI contract using Specmatic.

        Args:
            contract_path: Path to OpenAPI contract file

        Returns:
            SpecValidationResult with validation status
        """
        return await validate_spec_with_specmatic(contract_path)

    @beartype
    @require(lambda self, openapi_spec: isinstance(openapi_spec, dict), "OpenAPI spec must be dict")
    @require(lambda self, output_path: isinstance(output_path, Path), "Output path must be Path")
    @ensure(lambda result: result is None, "Must return None")
    def save_openapi_contract(self, openapi_spec: dict[str, Any], output_path: Path) -> None:
        """
        Save OpenAPI contract to file.

        Args:
            openapi_spec: OpenAPI specification dictionary
            output_path: Path to save contract file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            yaml.dump(openapi_spec, f, default_flow_style=False, sort_keys=False)
