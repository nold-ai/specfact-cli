"""Contract extractor for extracting API contracts from code signatures and validation logic.

Extracts contracts from function signatures, type hints, and validation logic,
generating OpenAPI/JSON Schema, icontract decorators, and contract test templates.
"""

from __future__ import annotations

import ast
from typing import Any

from beartype import beartype
from icontract import ensure, require


class ContractExtractor:
    """
    Extracts API contracts from function signatures, type hints, and validation logic.

    Generates:
    - Request/Response schemas from type hints
    - Preconditions from input validation
    - Postconditions from output validation
    - Error contracts from exception handling
    - OpenAPI/JSON Schema definitions
    - icontract decorators
    - Contract test templates
    """

    @beartype
    def __init__(self) -> None:
        """Initialize contract extractor."""

    @beartype
    @require(
        lambda method_node: isinstance(method_node, (ast.FunctionDef, ast.AsyncFunctionDef)),
        "Method must be function node",
    )
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def extract_function_contracts(self, method_node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, Any]:
        """
        Extract contracts from a function signature.

        Args:
            method_node: AST node for the function/method

        Returns:
            Dictionary containing:
            - parameters: List of parameter schemas
            - return_type: Return type schema
            - preconditions: List of preconditions
            - postconditions: List of postconditions
            - error_contracts: List of error contracts
        """
        contracts: dict[str, Any] = {
            "parameters": [],
            "return_type": None,
            "preconditions": [],
            "postconditions": [],
            "error_contracts": [],
        }

        # Extract parameters
        contracts["parameters"] = self._extract_parameters(method_node)

        # Extract return type
        contracts["return_type"] = self._extract_return_type(method_node)

        # Extract validation logic
        contracts["preconditions"] = self._extract_preconditions(method_node)
        contracts["postconditions"] = self._extract_postconditions(method_node)
        contracts["error_contracts"] = self._extract_error_contracts(method_node)

        return contracts

    @beartype
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def _extract_parameters(self, method_node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[dict[str, Any]]:
        """Extract parameter schemas from function signature."""
        parameters: list[dict[str, Any]] = []

        for arg in method_node.args.args:
            param: dict[str, Any] = {
                "name": arg.arg,
                "type": self._ast_to_type_string(arg.annotation) if arg.annotation else "Any",
                "required": True,
                "default": None,
            }

            # Check if parameter has default value
            # Default args are in method_node.args.defaults, aligned with last N args
            arg_index = method_node.args.args.index(arg)
            defaults_start = len(method_node.args.args) - len(method_node.args.defaults)
            if arg_index >= defaults_start:
                default_index = arg_index - defaults_start
                if default_index < len(method_node.args.defaults):
                    param["required"] = False
                    param["default"] = self._ast_to_value_string(method_node.args.defaults[default_index])

            parameters.append(param)

        # Handle *args
        if method_node.args.vararg:
            parameters.append(
                {
                    "name": method_node.args.vararg.arg,
                    "type": "list[Any]",
                    "required": False,
                    "variadic": True,
                }
            )

        # Handle **kwargs
        if method_node.args.kwarg:
            parameters.append(
                {
                    "name": method_node.args.kwarg.arg,
                    "type": "dict[str, Any]",
                    "required": False,
                    "keyword_variadic": True,
                }
            )

        return parameters

    @beartype
    @ensure(lambda result: result is None or isinstance(result, dict), "Must return None or dict")
    def _extract_return_type(self, method_node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, Any] | None:
        """Extract return type schema from function signature."""
        if not method_node.returns:
            return {"type": "None", "nullable": False}

        return {
            "type": self._ast_to_type_string(method_node.returns),
            "nullable": False,
        }

    @beartype
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def _extract_preconditions(self, method_node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
        """Extract preconditions from validation logic in function body."""
        preconditions: list[str] = []

        if not method_node.body:
            return preconditions

        for node in method_node.body:
            # Check for assertion statements
            if isinstance(node, ast.Assert):
                condition = self._ast_to_condition_string(node.test)
                preconditions.append(f"Requires: {condition}")

            # Check for validation decorators (would need to check decorator_list)
            # For now, we'll extract from docstrings and assertions

            # Check for isinstance checks
            if isinstance(node, ast.If):
                condition = self._ast_to_condition_string(node.test)
                # Check if it's a validation check (isinstance, type check, etc.)
                if "isinstance" in condition or "type" in condition.lower():
                    preconditions.append(f"Requires: {condition}")

        return preconditions

    @beartype
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def _extract_postconditions(self, method_node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
        """Extract postconditions from return value validation."""
        postconditions: list[str] = []

        if not method_node.body:
            return postconditions

        # Check for return statements with validation
        for node in ast.walk(ast.Module(body=list(method_node.body), type_ignores=[])):
            if isinstance(node, ast.Return) and node.value:
                return_type = self._ast_to_type_string(method_node.returns) if method_node.returns else "Any"
                postconditions.append(f"Ensures: returns {return_type}")

        return postconditions

    @beartype
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def _extract_error_contracts(self, method_node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[dict[str, Any]]:
        """Extract error contracts from exception handling."""
        error_contracts: list[dict[str, Any]] = []

        if not method_node.body:
            return error_contracts

        for node in method_node.body:
            if isinstance(node, ast.Try):
                for handler in node.handlers:
                    exception_type = "Exception"
                    if handler.type:
                        exception_type = self._ast_to_type_string(handler.type)

                    error_contracts.append(
                        {
                            "exception_type": exception_type,
                            "condition": self._ast_to_condition_string(handler.type)
                            if handler.type
                            else "Any exception",
                        }
                    )

            # Check for raise statements
            for child in ast.walk(node):
                if (
                    isinstance(child, ast.Raise)
                    and child.exc
                    and isinstance(child.exc, ast.Call)
                    and isinstance(child.exc.func, ast.Name)
                ):
                    error_contracts.append(
                        {
                            "exception_type": child.exc.func.id,
                            "condition": "Error condition",
                        }
                    )

        return error_contracts

    @beartype
    @ensure(lambda result: isinstance(result, str), "Must return string")
    def _ast_to_type_string(self, node: ast.AST | None) -> str:
        """Convert AST type annotation node to string representation."""
        if node is None:
            return "Any"

        # Use ast.unparse if available (Python 3.9+)
        if hasattr(ast, "unparse"):
            try:
                return ast.unparse(node)
            except Exception:
                pass

        # Fallback: manual conversion
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
            # Handle generics like List[str], Dict[str, int], Optional[str]
            container = node.value.id
            if isinstance(node.slice, ast.Tuple):
                args = [self._ast_to_type_string(el) for el in node.slice.elts]
                return f"{container}[{', '.join(args)}]"
            if isinstance(node.slice, ast.Name):
                return f"{container}[{node.slice.id}]"
            return f"{container}[...]"
        if isinstance(node, ast.Constant):
            return str(node.value)

        return "Any"

    @beartype
    @ensure(lambda result: isinstance(result, str), "Must return string")
    def _ast_to_value_string(self, node: ast.AST) -> str:
        """Convert AST value node to string representation."""
        if isinstance(node, ast.Constant):
            return repr(node.value)
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.NameConstant):  # Python < 3.8
            return str(node.value)

        # Use ast.unparse if available
        if hasattr(ast, "unparse"):
            try:
                return ast.unparse(node)
            except Exception:
                pass

        return "..."

    @beartype
    @ensure(lambda result: isinstance(result, str), "Must return string")
    def _ast_to_condition_string(self, node: ast.AST) -> str:
        """Convert AST condition node to string representation."""
        # Use ast.unparse if available
        if hasattr(ast, "unparse"):
            try:
                return ast.unparse(node)
            except Exception:
                pass

        # Fallback: basic conversion
        if isinstance(node, ast.Compare):
            left = self._ast_to_condition_string(node.left) if hasattr(node, "left") else "..."
            ops = [self._op_to_string(op) for op in node.ops]
            comparators = [self._ast_to_condition_string(comp) for comp in node.comparators]
            return f"{left} {' '.join(ops)} {' '.join(comparators)}"
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            args = [self._ast_to_condition_string(arg) for arg in node.args]
            return f"{node.func.id}({', '.join(args)})"
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Constant):
            return repr(node.value)

        return "..."

    @beartype
    @ensure(lambda result: isinstance(result, str), "Must return string")
    def _op_to_string(self, op: ast.cmpop) -> str:
        """Convert AST comparison operator to string."""
        op_map = {
            ast.Eq: "==",
            ast.NotEq: "!=",
            ast.Lt: "<",
            ast.LtE: "<=",
            ast.Gt: ">",
            ast.GtE: ">=",
            ast.Is: "is",
            ast.IsNot: "is not",
            ast.In: "in",
            ast.NotIn: "not in",
        }
        return op_map.get(type(op), "??")

    @beartype
    @require(lambda contracts: isinstance(contracts, dict), "Contracts must be dict")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def generate_json_schema(self, contracts: dict[str, Any]) -> dict[str, Any]:
        """
        Generate JSON Schema from contracts.

        Args:
            contracts: Contract dictionary from extract_function_contracts()

        Returns:
            JSON Schema dictionary
        """
        schema: dict[str, Any] = {
            "type": "object",
            "properties": {},
            "required": [],
        }

        # Add parameter properties
        for param in contracts.get("parameters", []):
            param_name = param["name"]
            param_type = param.get("type", "Any")
            schema["properties"][param_name] = self._type_to_json_schema(param_type)

            if param.get("required", True):
                schema["required"].append(param_name)

        return schema

    @beartype
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def _type_to_json_schema(self, type_str: str) -> dict[str, Any]:
        """Convert Python type string to JSON Schema type."""
        type_str = type_str.strip()

        # Basic types
        if type_str == "str":
            return {"type": "string"}
        if type_str == "int":
            return {"type": "integer"}
        if type_str == "float":
            return {"type": "number"}
        if type_str == "bool":
            return {"type": "boolean"}
        if type_str == "None" or type_str == "NoneType":
            return {"type": "null"}

        # Optional types
        if type_str.startswith("Optional[") or (type_str.startswith("Union[") and "None" in type_str):
            inner_type = type_str.split("[")[1].rstrip("]").split(",")[0].strip()
            if "None" in inner_type:
                inner_type = next(
                    (t.strip() for t in type_str.split("[")[1].rstrip("]").split(",") if "None" not in t),
                    inner_type,
                )
            return {"anyOf": [self._type_to_json_schema(inner_type), {"type": "null"}]}

        # List types
        if type_str.startswith(("list[", "List[")):
            inner_type = type_str.split("[")[1].rstrip("]")
            return {"type": "array", "items": self._type_to_json_schema(inner_type)}

        # Dict types
        if type_str.startswith(("dict[", "Dict[")):
            parts = type_str.split("[")[1].rstrip("]").split(",")
            if len(parts) >= 2:
                value_type = parts[1].strip()
                return {"type": "object", "additionalProperties": self._type_to_json_schema(value_type)}

        # Default: any type
        return {"type": "object"}

    @beartype
    @require(lambda contracts: isinstance(contracts, dict), "Contracts must be dict")
    @ensure(lambda result: isinstance(result, str), "Must return string")
    def generate_icontract_decorator(self, contracts: dict[str, Any], function_name: str) -> str:
        """
        Generate icontract decorator code from contracts.

        Args:
            contracts: Contract dictionary from extract_function_contracts()
            function_name: Name of the function

        Returns:
            Python code string with icontract decorators
        """
        decorators: list[str] = []

        # Generate @require decorators from preconditions
        for precondition in contracts.get("preconditions", []):
            condition = precondition.replace("Requires: ", "")
            decorators.append(f'@require(lambda: {condition}, "{precondition}")')

        # Generate @ensure decorators from postconditions
        for postcondition in contracts.get("postconditions", []):
            condition = postcondition.replace("Ensures: ", "")
            decorators.append(f'@ensure(lambda result: {condition}, "{postcondition}")')

        return "\n".join(decorators) if decorators else ""
