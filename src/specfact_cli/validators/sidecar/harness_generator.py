"""
Harness generation logic for sidecar validation.

This module generates CrossHair harness files from OpenAPI contracts.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml
from beartype import beartype
from icontract import ensure, require


@beartype
@require(lambda contracts_dir: contracts_dir.exists(), "Contracts directory must exist")
@require(lambda harness_path: isinstance(harness_path, Path), "Harness path must be Path")
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def generate_harness(contracts_dir: Path, harness_path: Path) -> bool:
    """
    Generate CrossHair harness from OpenAPI contracts.

    Args:
        contracts_dir: Directory containing OpenAPI contract files
        harness_path: Path to output harness file

    Returns:
        True if harness was generated successfully
    """
    contract_files = list(contracts_dir.glob("*.yaml")) + list(contracts_dir.glob("*.yml"))
    if not contract_files:
        return False

    operations: list[dict[str, Any]] = []

    for contract_file in contract_files:
        try:
            with contract_file.open(encoding="utf-8") as f:
                contract_data = yaml.safe_load(f) or {}

            ops = extract_operations(contract_data)
            operations.extend(ops)
        except Exception:
            continue

    if not operations:
        return False

    harness_content = render_harness(operations)
    harness_path.parent.mkdir(parents=True, exist_ok=True)
    harness_path.write_text(harness_content, encoding="utf-8")

    return True


@beartype
@require(lambda contract_data: isinstance(contract_data, dict), "Contract data must be dict")
@ensure(lambda result: isinstance(result, list), "Must return list")
def extract_operations(contract_data: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Extract operations from OpenAPI contract.

    Args:
        contract_data: Contract data dictionary

    Returns:
        List of operation dictionaries
    """
    operations: list[dict[str, Any]] = []

    paths = contract_data.get("paths", {})
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        for method, operation in path_item.items():
            if method.lower() not in ("get", "post", "put", "patch", "delete"):
                continue

            if not isinstance(operation, dict):
                continue

            op_id = operation.get("operationId") or f"{method}_{path}"
            operations.append(
                {
                    "operation_id": op_id,
                    "path": path,
                    "method": method.upper(),
                    "request_schema": operation.get("requestBody", {}),
                    "response_schema": operation.get("responses", {}),
                }
            )

    return operations


@beartype
@require(lambda operations: isinstance(operations, list), "Operations must be a list")
@ensure(lambda result: isinstance(result, str), "Must return str")
def render_harness(operations: list[dict[str, Any]]) -> str:
    """
    Render harness Python code from operations.

    Args:
        operations: List of operation dictionaries

    Returns:
        Harness Python code as string
    """
    lines: list[str] = []
    lines.append('"""Generated sidecar harness for CrossHair validation."""')
    lines.append("from __future__ import annotations")
    lines.append("")
    lines.append("from typing import Any")
    lines.append("")
    lines.append("from beartype import beartype")
    lines.append("from icontract import ensure, require")
    lines.append("")
    lines.append("try:")
    lines.append("    from common import adapters as sidecar_adapters")
    lines.append("except ImportError:")
    lines.append("    sidecar_adapters = None")
    lines.append("")

    for op in operations:
        op_id = op["operation_id"]
        method = op["method"]
        path = op["path"]

        # Sanitize operation_id to create valid Python function name
        # Replace all non-identifier characters (/, {, }, -, ., etc.) with underscore
        sanitized_id = re.sub(r"[^a-zA-Z0-9_]", "_", op_id)
        func_name = f"harness_{sanitized_id}"
        lines.append("")
        lines.append("@beartype")
        lines.append("@require(lambda *args, **kwargs: True, 'Precondition placeholder')")
        lines.append("@ensure(lambda result: True, 'Postcondition placeholder')")
        lines.append(f"def {func_name}(*args: Any, **kwargs: Any) -> Any:")
        lines.append(f'    """Harness for {method} {path}."""')
        lines.append("    if sidecar_adapters:")
        lines.append(f"        return sidecar_adapters.call_endpoint('{method}', '{path}', *args, **kwargs)")
        lines.append("    return None")
        lines.append("")

    return "\n".join(lines)
