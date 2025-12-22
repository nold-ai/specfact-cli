#!/usr/bin/env python3
"""
Generate deterministic CrossHair harness and inputs from OpenAPI contracts.
"""

from __future__ import annotations

import argparse
import json
import pprint
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


METHOD_ORDER = ["get", "post", "put", "patch", "delete", "options", "head", "trace"]


def _python_literal(value: Any) -> str:
    return pprint.pformat(value, width=120, sort_dicts=True)


def _base_type_name(type_str: str) -> str:
    candidates = [part.strip() for part in type_str.split("|") if part.strip()]
    for candidate in candidates:
        if candidate in {"None", "NoneType"}:
            continue
        return re.split(r"[\[( ]", candidate, maxsplit=1)[0]
    return candidates[0] if candidates else type_str


def _sorted_methods(methods: list[str]) -> list[str]:
    method_rank = {name: index for index, name in enumerate(METHOD_ORDER)}
    return sorted(methods, key=lambda name: (method_rank.get(name, 99), name))


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _resolve_ref(ref: str, doc: dict[str, Any]) -> dict[str, Any] | None:
    if not ref.startswith("#/"):
        return None
    parts = [part for part in ref.lstrip("#/").split("/") if part]
    node: Any = doc
    for part in parts:
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    if isinstance(node, dict):
        return deepcopy(node)
    return None


def _merge_schemas(schemas: list[dict[str, Any]]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for schema in schemas:
        for key, value in schema.items():
            if key == "required":
                existing = set(merged.get("required", []))
                existing.update(value or [])
                merged["required"] = sorted(existing)
            elif key == "properties":
                props = merged.setdefault("properties", {})
                for prop_key, prop_value in (value or {}).items():
                    props[prop_key] = prop_value
            elif key == "allOf":
                continue
            else:
                merged.setdefault(key, value)
    return merged


def _normalize_schema(schema: dict[str, Any], doc: dict[str, Any], depth: int = 0) -> dict[str, Any]:
    if depth > 10:
        return schema
    if "$ref" in schema:
        resolved = _resolve_ref(schema["$ref"], doc)
        if resolved is None:
            return schema
        return _normalize_schema(resolved, doc, depth + 1)

    schema = deepcopy(schema)

    if "allOf" in schema:
        merged = _merge_schemas([_normalize_schema(item, doc, depth + 1) for item in schema["allOf"]])
        schema.pop("allOf", None)
        schema = _merge_schemas([merged, schema])

    for key in ("oneOf", "anyOf"):
        if key in schema:
            schema[key] = [_normalize_schema(item, doc, depth + 1) for item in schema[key]]

    if "properties" in schema:
        schema["properties"] = {
            prop_key: _normalize_schema(prop_value, doc, depth + 1)
            for prop_key, prop_value in schema["properties"].items()
        }

    if "items" in schema and isinstance(schema["items"], dict):
        schema["items"] = _normalize_schema(schema["items"], doc, depth + 1)

    return schema


def _example_from_schema(schema: dict[str, Any]) -> Any:
    if "example" in schema:
        return schema["example"]
    if "default" in schema:
        return schema["default"]
    if "enum" in schema:
        return schema["enum"][0] if schema["enum"] else None

    schema_type = schema.get("type")
    if schema_type == "object":
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))
        result: dict[str, Any] = {}
        for key in sorted(required):
            if key in properties:
                result[key] = _example_from_schema(properties[key])
        return result
    if schema_type == "array":
        item_schema = schema.get("items", {})
        return [_example_from_schema(item_schema)] if item_schema else []
    if schema_type == "string":
        return "example"
    if schema_type == "integer":
        return 0
    if schema_type == "number":
        return 0.0
    if schema_type == "boolean":
        return True
    return None


def _sanitize_identifier(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip("/"))
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    if not normalized:
        return "root"
    if normalized[0].isdigit():
        return f"op_{normalized}"
    return normalized.lower()


def _extract_request_schema(operation: dict[str, Any], doc: dict[str, Any]) -> dict[str, Any]:
    request_body = operation.get("requestBody", {})
    content = request_body.get("content", {})
    json_content = content.get("application/json") or {}
    schema = json_content.get("schema", {})
    if not schema:
        return {}
    return _normalize_schema(schema, doc)


def _extract_response_schema(operation: dict[str, Any], doc: dict[str, Any]) -> dict[str, Any]:
    responses = operation.get("responses", {})
    for status_code in sorted(responses.keys()):
        if not str(status_code).startswith("2"):
            continue
        response = responses[status_code] or {}
        content = response.get("content", {})
        json_content = content.get("application/json") or {}
        schema = json_content.get("schema", {})
        if schema:
            return _normalize_schema(schema, doc)
    return {}


def _extract_operation_examples(
    request_schema: dict[str, Any], response_schema: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    return (
        _example_from_schema(request_schema) if request_schema else {},
        _example_from_schema(response_schema) if response_schema else {},
    )


def _collect_operations(contracts_dir: Path) -> list[dict[str, Any]]:
    operations: list[dict[str, Any]] = []
    for contract_file in sorted(contracts_dir.glob("*.openapi.yaml")):
        doc = _load_yaml(contract_file)
        paths = doc.get("paths", {}) if isinstance(doc, dict) else {}
        for path, path_item in sorted(paths.items()):
            if not isinstance(path_item, dict):
                continue
            methods = [method for method in path_item if method.lower() in METHOD_ORDER]
            for method in _sorted_methods([method.lower() for method in methods]):
                operation = path_item.get(method, {}) if isinstance(path_item, dict) else {}
                request_schema = _extract_request_schema(operation, doc)
                response_schema = _extract_response_schema(operation, doc)
                request_example, response_example = _extract_operation_examples(request_schema, response_schema)
                op_id = operation.get("operationId") or f"{method}_{path}"
                operations.append(
                    {
                        "operation_id": op_id,
                        "path": path,
                        "method": method,
                        "request_schema": request_schema,
                        "response_schema": response_schema,
                        "request_example": request_example,
                        "response_example": response_example,
                    }
                )
    return operations


def _load_feature_contracts(features_dir: Path) -> dict[str, dict[str, Any]]:
    contracts: dict[str, dict[str, Any]] = {}
    if not features_dir.exists():
        return contracts
    for feature_file in sorted(features_dir.glob("FEATURE-*.yaml")):
        feature = _load_yaml(feature_file)
        if not isinstance(feature, dict):
            continue
        source_functions = feature.get("source_functions", []) or []
        func_names = []
        for source in source_functions:
            if "::" in source:
                func_names.append(source.split("::")[-1])
        stories = feature.get("stories", []) or []
        for story in stories:
            contract = story.get("contracts") or {}
            if not contract:
                continue
            return_type = contract.get("return_type") or {}
            return_type_str = return_type.get("type")
            nullable = return_type.get("nullable", True)
            required_params = [
                param.get("name")
                for param in (contract.get("parameters") or [])
                if param.get("required") and param.get("name") and param.get("name") != "self"
            ]
            for func_name in func_names:
                entry = contracts.setdefault(
                    func_name,
                    {"required_params": set(), "return_type": None, "nullable": True},
                )
                entry["required_params"].update(required_params)
                if return_type_str and entry["return_type"] is None:
                    entry["return_type"] = return_type_str
                if nullable is False:
                    entry["nullable"] = False
    return contracts


def _load_bindings(bindings_path: Path) -> dict[str, dict[str, Any]]:
    bindings: dict[str, dict[str, Any]] = {}
    if not bindings_path.exists():
        return bindings
    data = _load_yaml(bindings_path)
    if not isinstance(data, dict):
        return bindings
    for entry in data.get("bindings", []) or []:
        if not isinstance(entry, dict):
            continue
        key = entry.get("operation_id") or entry.get("function_name")
        if not key:
            continue
        payload = dict(entry)
        payload.setdefault("call_style", "dict")
        bindings[key] = payload
    return bindings


def _render_harness(
    operations: list[dict[str, Any]],
    feature_contracts: dict[str, dict[str, Any]],
    bindings: dict[str, dict[str, Any]],
) -> str:
    lines: list[str] = []
    lines.append('"""Generated sidecar harness (deterministic)."""')
    lines.append("from __future__ import annotations")
    lines.append("")
    lines.append("from functools import lru_cache")
    lines.append("from typing import Any, Callable")
    lines.append("")
    lines.append("from beartype import beartype")
    lines.append("from icontract import ensure, require")
    lines.append("")
    lines.append("import importlib")
    lines.append("import os")
    lines.append("import adapters as sidecar_adapters")
    lines.append("")
    lines.append("")
    lines.append("@lru_cache(maxsize=None)")
    lines.append("def _load_binding(target: str) -> Callable[..., Any]:")
    lines.append('    module_name, func_name = target.split(":", 1)')
    lines.append("    module = importlib.import_module(module_name)")
    lines.append("    return getattr(module, func_name)")
    lines.append("")
    lines.append("def _matches_schema(value: Any, schema: dict[str, Any]) -> bool:")
    lines.append("    if not schema:")
    lines.append("        return True")
    lines.append('    if schema.get("nullable") and value is None:')
    lines.append("        return True")
    lines.append('    if "enum" in schema and value not in schema.get("enum", []):')
    lines.append("        return False")
    lines.append('    schema_type = schema.get("type")')
    lines.append('    if schema_type == "object":')
    lines.append("        if not isinstance(value, dict):")
    lines.append("            return False")
    lines.append('        required = schema.get("required", [])')
    lines.append("        for key in required:")
    lines.append("            if key not in value:")
    lines.append("                return False")
    lines.append('        properties = schema.get("properties", {})')
    lines.append("        for key, prop_schema in properties.items():")
    lines.append("            if key in value and not _matches_schema(value[key], prop_schema):")
    lines.append("                return False")
    lines.append("        return True")
    lines.append('    if schema_type == "array":')
    lines.append("        if not isinstance(value, list):")
    lines.append("            return False")
    lines.append('        min_items = schema.get("minItems")')
    lines.append('        max_items = schema.get("maxItems")')
    lines.append("        if min_items is not None and len(value) < min_items:")
    lines.append("            return False")
    lines.append("        if max_items is not None and len(value) > max_items:")
    lines.append("            return False")
    lines.append('        item_schema = schema.get("items", {})')
    lines.append("        return all(_matches_schema(item, item_schema) for item in value)")
    lines.append('    if schema_type == "string":')
    lines.append("        if not isinstance(value, str):")
    lines.append("            return False")
    lines.append('        min_len = schema.get("minLength")')
    lines.append('        max_len = schema.get("maxLength")')
    lines.append("        if min_len is not None and len(value) < min_len:")
    lines.append("            return False")
    lines.append("        if max_len is not None and len(value) > max_len:")
    lines.append("            return False")
    lines.append("        return True")
    lines.append('    if schema_type == "integer":')
    lines.append("        if not isinstance(value, int):")
    lines.append("            return False")
    lines.append('        minimum = schema.get("minimum")')
    lines.append('        maximum = schema.get("maximum")')
    lines.append("        if minimum is not None and value < minimum:")
    lines.append("            return False")
    lines.append("        if maximum is not None and value > maximum:")
    lines.append("            return False")
    lines.append("        return True")
    lines.append('    if schema_type == "number":')
    lines.append("        if not isinstance(value, (int, float)):")
    lines.append("            return False")
    lines.append('        minimum = schema.get("minimum")')
    lines.append('        maximum = schema.get("maximum")')
    lines.append("        if minimum is not None and value < minimum:")
    lines.append("            return False")
    lines.append("        if maximum is not None and value > maximum:")
    lines.append("            return False")
    lines.append("        return True")
    lines.append('    if schema_type == "boolean":')
    lines.append("        return isinstance(value, bool)")
    lines.append('    any_of = schema.get("anyOf") or schema.get("oneOf")')
    lines.append("    if any_of:")
    lines.append("        return any(_matches_schema(value, item) for item in any_of)")
    lines.append('    all_of = schema.get("allOf")')
    lines.append("    if all_of:")
    lines.append("        return all(_matches_schema(value, item) for item in all_of)")
    lines.append("    return True")
    lines.append("")
    lines.append("def _request_has_required(request: Any, required: list[str]) -> bool:")
    lines.append("    if not required:")
    lines.append("        return True")
    lines.append("    if not isinstance(request, dict):")
    lines.append("        return False")
    lines.append("    for key in required:")
    lines.append("        if key not in request or request[key] is None:")
    lines.append("            return False")
    lines.append("    return True")
    lines.append("")
    lines.append("")
    lines.append("def _matches_return_contract(value: Any, contract: dict[str, Any]) -> bool:")
    lines.append("    if not contract:")
    lines.append("        return True")
    lines.append("    nullable = contract.get('nullable', True)")
    lines.append("    if value is None:")
    lines.append("        return nullable")
    lines.append("    expected = contract.get('type')")
    lines.append("    if not expected:")
    lines.append("        return True")
    lines.append("    expected = expected.split('|')[0].strip()")
    lines.append("    expected = expected.split('[', 1)[0].split('(', 1)[0]")
    lines.append("    type_map = {'str': str, 'int': int, 'float': float, 'bool': bool, 'dict': dict, 'list': list}")
    lines.append("    if expected in {'None', 'NoneType'}:")
    lines.append("        return value is None")
    lines.append("    py_type = type_map.get(expected)")
    lines.append("    if py_type:")
    lines.append("        return isinstance(value, py_type)")
    lines.append("    return True")
    lines.append("")
    lines.append("")
    lines.append("def _resolve_value(value: Any, request: Any) -> Any:")
    lines.append("    if isinstance(value, str):")
    lines.append("        if value.startswith('$request.') and isinstance(request, dict):")
    lines.append("            return request.get(value.split('.', 1)[1])")
    lines.append("        if value.startswith('$env.'):")
    lines.append("            return os.environ.get(value.split('.', 1)[1])")
    lines.append("    return value")
    lines.append("")
    lines.append("")
    lines.append("def _resolve_list(values: list[Any], request: Any) -> list[Any]:")
    lines.append("    return [_resolve_value(item, request) for item in values]")
    lines.append("")
    lines.append("")
    lines.append("def _resolve_dict(values: dict[str, Any], request: Any) -> dict[str, Any]:")
    lines.append("    return {key: _resolve_value(value, request) for key, value in values.items()}")
    lines.append("")
    lines.append("")
    lines.append("def _call_target(target: Callable[..., Any], call_style: str, request: Any, args: list[str]) -> Any:")
    lines.append("    if call_style == 'none':")
    lines.append("        return target()")
    lines.append("    if call_style == 'kwargs':")
    lines.append("        payload = request if isinstance(request, dict) else {}")
    lines.append("        return target(**payload)")
    lines.append("    if call_style == 'args':")
    lines.append("        payload = request if isinstance(request, dict) else {}")
    lines.append("        resolved = [payload.get(name) for name in args]")
    lines.append("        return target(*resolved)")
    lines.append("    return target(request)")
    lines.append("")
    lines.append("")
    lines.append("def _execute_binding(binding: dict[str, Any], request: Any) -> Any:")
    lines.append("    adapter_name = binding.get('adapter')")
    lines.append("    if adapter_name:")
    lines.append("        adapter = getattr(sidecar_adapters, adapter_name, None)")
    lines.append("        if adapter is None:")
    lines.append("            raise ValueError(f'Unknown adapter: {adapter_name}')")
    lines.append("        return adapter(binding, request, _load_binding, _call_target, _resolve_value)")
    lines.append("    target_name = binding.get('target') or binding.get('function')")
    lines.append("    if not target_name:")
    lines.append("        raise ValueError('Binding missing target')")
    lines.append("    call_style = binding.get('call_style', 'dict')")
    lines.append("    args = binding.get('args', [])")
    lines.append("    method_name = binding.get('method')")
    lines.append("    factory_cfg = binding.get('factory') or {}")
    lines.append("    if method_name:")
    lines.append("        factory_target_name = factory_cfg.get('target') or target_name")
    lines.append("        factory_target = _load_binding(factory_target_name)")
    lines.append("        factory_args = _resolve_list(factory_cfg.get('args', []), request)")
    lines.append("        factory_kwargs = _resolve_dict(factory_cfg.get('kwargs', {}), request)")
    lines.append("        instance = factory_target(*factory_args, **factory_kwargs)")
    lines.append("        method = getattr(instance, method_name)")
    lines.append("        return _call_target(method, call_style, request, args)")
    lines.append("    target = _load_binding(target_name)")
    lines.append("    return _call_target(target, call_style, request, args)")
    lines.append("")
    lines.append("")

    for operation in operations:
        func_name = _sanitize_identifier(f"{operation['method']}_{operation['path']}")
        op_id = operation["operation_id"]
        request_schema = operation["request_schema"]
        response_schema = operation["response_schema"]
        response_example = operation["response_example"]
        feature = feature_contracts.get(op_id) or feature_contracts.get(func_name) or {}
        binding = bindings.get(op_id) or bindings.get(func_name) or {}
        binding_target = binding.get("target") or binding.get("function")
        required_params = sorted(feature.get("required_params", []))
        return_contract: dict[str, Any] = {}
        if feature.get("return_type") or feature.get("nullable") is False:
            return_contract = {
                "type": _base_type_name(feature["return_type"]) if feature.get("return_type") else "",
                "nullable": feature.get("nullable", True),
            }
        lines.append(f"REQUEST_SCHEMA_{func_name.upper()} = {_python_literal(request_schema)}")
        lines.append(f"RESPONSE_SCHEMA_{func_name.upper()} = {_python_literal(response_schema)}")
        lines.append(f"RESPONSE_EXAMPLE_{func_name.upper()} = {_python_literal(response_example)}")
        if required_params:
            lines.append(f"FEATURE_REQUIRED_{func_name.upper()} = {_python_literal(required_params)}")
        if return_contract:
            lines.append(f"FEATURE_RETURN_CONTRACT_{func_name.upper()} = {_python_literal(return_contract)}")
        if binding and binding_target:
            lines.append(f"BINDING_{func_name.upper()} = {_python_literal(binding)}")
        lines.append("")
        lines.append(f"@require(lambda request: _matches_schema(request, REQUEST_SCHEMA_{func_name.upper()}))")
        if required_params:
            lines.append(
                f"@require(lambda request: _request_has_required(request, FEATURE_REQUIRED_{func_name.upper()}))"
            )
        lines.append(f"@ensure(lambda result: _matches_schema(result, RESPONSE_SCHEMA_{func_name.upper()}))")
        if return_contract:
            lines.append(
                f"@ensure(lambda result: _matches_return_contract(result, FEATURE_RETURN_CONTRACT_{func_name.upper()}))"
            )
        lines.append("@beartype")
        lines.append(f"def {func_name}(request: Any) -> Any:")
        lines.append('    """Generated operation harness."""')
        if binding and binding_target:
            lines.append(f"    return _execute_binding(BINDING_{func_name.upper()}, request)")
        else:
            lines.append(f"    return RESPONSE_EXAMPLE_{func_name.upper()}")
        lines.append("")

    lines.append("__all__ = [")
    for operation in operations:
        func_name = _sanitize_identifier(f"{operation['method']}_{operation['path']}")
        lines.append(f'    "{func_name}",')
    lines.append("]")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic sidecar harness from OpenAPI contracts.")
    parser.add_argument("--contracts", required=True, help="Contracts directory containing *.openapi.yaml files")
    parser.add_argument("--output", required=True, help="Output harness path")
    parser.add_argument("--inputs", required=True, help="Output inputs JSON path")
    parser.add_argument("--features", help="Features directory containing FEATURE-*.yaml files")
    parser.add_argument("--bindings", help="Bindings YAML mapping operation_ids to functions")
    args = parser.parse_args()

    contracts_dir = Path(args.contracts)
    if not contracts_dir.exists():
        raise SystemExit(f"Contracts directory not found: {contracts_dir}")

    operations = _collect_operations(contracts_dir)
    features_dir = Path(args.features) if args.features else contracts_dir.parent / "features"
    bindings_path = Path(args.bindings) if args.bindings else Path("bindings.yaml")
    feature_contracts = _load_feature_contracts(features_dir)
    bindings = _load_bindings(bindings_path)
    inputs_payload = {
        "operations": [
            {
                "operation_id": op["operation_id"],
                "method": op["method"],
                "path": op["path"],
                "request": op["request_example"],
                "response": op["response_example"],
            }
            for op in operations
        ]
    }

    Path(args.inputs).write_text(json.dumps(inputs_payload, sort_keys=True, indent=2), encoding="utf-8")
    Path(args.output).write_text(_render_harness(operations, feature_contracts, bindings), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
