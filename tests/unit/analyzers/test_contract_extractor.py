"""Unit tests for contract extractor.

Focus: Business logic and edge cases only (@beartype handles type validation).
"""

import ast
from textwrap import dedent

from specfact_cli.analyzers.contract_extractor import ContractExtractor


def _get_function_node(tree: ast.Module) -> ast.FunctionDef | ast.AsyncFunctionDef:
    """Extract function node from AST module."""
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return node
    raise ValueError("No function found in AST")


class TestContractExtractor:
    """Test suite for ContractExtractor."""

    def test_extract_function_contracts_basic(self):
        """Test extracting contracts from a basic function."""
        code = dedent(
            """
            def add(a: int, b: int) -> int:
                return a + b
            """
        )
        tree = ast.parse(code)
        func_node = _get_function_node(tree)

        extractor = ContractExtractor()
        contracts = extractor.extract_function_contracts(func_node)

        assert isinstance(contracts, dict)
        assert "parameters" in contracts
        assert "return_type" in contracts
        assert "preconditions" in contracts
        assert "postconditions" in contracts
        assert "error_contracts" in contracts

        # Check parameters
        assert len(contracts["parameters"]) == 2
        assert contracts["parameters"][0]["name"] == "a"
        assert contracts["parameters"][0]["type"] == "int"
        assert contracts["parameters"][0]["required"] is True
        assert contracts["parameters"][1]["name"] == "b"
        assert contracts["parameters"][1]["type"] == "int"

        # Check return type
        assert contracts["return_type"] is not None
        assert contracts["return_type"]["type"] == "int"

    def test_extract_function_contracts_with_defaults(self):
        """Test extracting contracts from function with default parameters."""
        code = dedent(
            """
            def greet(name: str, greeting: str = "Hello") -> str:
                return f"{greeting}, {name}!"
            """
        )
        tree = ast.parse(code)
        func_node = _get_function_node(tree)

        extractor = ContractExtractor()
        contracts = extractor.extract_function_contracts(func_node)

        # Check parameters
        assert len(contracts["parameters"]) == 2
        assert contracts["parameters"][0]["name"] == "name"
        assert contracts["parameters"][0]["required"] is True
        assert contracts["parameters"][1]["name"] == "greeting"
        assert contracts["parameters"][1]["required"] is False
        assert contracts["parameters"][1]["default"] is not None

    def test_extract_function_contracts_with_preconditions(self):
        """Test extracting preconditions from validation logic."""
        code = dedent(
            """
            def divide(a: float, b: float) -> float:
                assert b != 0, "Division by zero"
                if a < 0:
                    raise ValueError("Negative not allowed")
                return a / b
            """
        )
        tree = ast.parse(code)
        func_node = _get_function_node(tree)

        extractor = ContractExtractor()
        contracts = extractor.extract_function_contracts(func_node)

        # Check preconditions
        assert len(contracts["preconditions"]) > 0
        assert any("b != 0" in str(p) or "b" in str(p) for p in contracts["preconditions"])

        # Check error contracts
        assert len(contracts["error_contracts"]) > 0
        assert any("ValueError" in str(e) for e in contracts["error_contracts"])

    def test_extract_function_contracts_with_postconditions(self):
        """Test extracting postconditions from return validation."""
        code = dedent(
            """
            def get_positive(value: int) -> int:
                result = abs(value)
                assert result >= 0
                return result
            """
        )
        tree = ast.parse(code)
        func_node = _get_function_node(tree)

        extractor = ContractExtractor()
        contracts = extractor.extract_function_contracts(func_node)

        # Check postconditions
        assert len(contracts["postconditions"]) > 0
        assert any("returns" in str(p).lower() or "int" in str(p) for p in contracts["postconditions"])

    def test_extract_function_contracts_with_error_handling(self):
        """Test extracting error contracts from try/except blocks."""
        code = dedent(
            """
            def process_data(data: str) -> dict:
                try:
                    return {"result": data.upper()}
                except AttributeError as e:
                    raise ValueError("Invalid data") from e
            """
        )
        tree = ast.parse(code)
        func_node = _get_function_node(tree)

        extractor = ContractExtractor()
        contracts = extractor.extract_function_contracts(func_node)

        # Check error contracts
        assert len(contracts["error_contracts"]) > 0
        error_types = [e.get("exception_type", "") for e in contracts["error_contracts"]]
        assert any("AttributeError" in str(e) or "ValueError" in str(e) for e in error_types)

    def test_extract_function_contracts_complex_types(self):
        """Test extracting contracts from function with complex types."""
        code = dedent(
            """
            def process_items(items: list[str], config: dict[str, int]) -> list[dict]:
                return [{"item": item, "count": config.get(item, 0)} for item in items]
            """
        )
        tree = ast.parse(code)
        func_node = _get_function_node(tree)

        extractor = ContractExtractor()
        contracts = extractor.extract_function_contracts(func_node)

        # Check parameters with complex types
        assert len(contracts["parameters"]) == 2
        items_param = next(p for p in contracts["parameters"] if p["name"] == "items")
        assert "list" in items_param["type"].lower() or "List" in items_param["type"]

        config_param = next(p for p in contracts["parameters"] if p["name"] == "config")
        assert "dict" in config_param["type"].lower() or "Dict" in config_param["type"]

    def test_extract_function_contracts_async_function(self):
        """Test extracting contracts from async function."""
        code = dedent(
            """
            async def fetch_data(url: str) -> dict:
                return {"data": "result"}
            """
        )
        tree = ast.parse(code)
        func_node = _get_function_node(tree)

        extractor = ContractExtractor()
        contracts = extractor.extract_function_contracts(func_node)

        assert isinstance(contracts, dict)
        assert len(contracts["parameters"]) == 1
        assert contracts["parameters"][0]["name"] == "url"
        assert contracts["return_type"] is not None

    def test_extract_function_contracts_no_type_hints(self):
        """Test extracting contracts from function without type hints."""
        code = dedent(
            """
            def process(data):
                return data.upper()
            """
        )
        tree = ast.parse(code)
        func_node = _get_function_node(tree)

        extractor = ContractExtractor()
        contracts = extractor.extract_function_contracts(func_node)

        assert isinstance(contracts, dict)
        assert len(contracts["parameters"]) == 1
        assert contracts["parameters"][0]["type"] == "Any"  # Default when no type hint

    def test_extract_function_contracts_optional_types(self):
        """Test extracting contracts from function with Optional types."""
        code = dedent(
            """
            def get_value(key: str, default: str | None = None) -> str | None:
                return default
            """
        )
        tree = ast.parse(code)
        func_node = _get_function_node(tree)

        extractor = ContractExtractor()
        contracts = extractor.extract_function_contracts(func_node)

        # Check that Optional is handled
        assert len(contracts["parameters"]) == 2
        default_param = next(p for p in contracts["parameters"] if p["name"] == "default")
        assert default_param["required"] is False

    def test_extract_function_contracts_self_parameter(self):
        """Test that self parameter is handled correctly."""
        code = dedent(
            """
            class MyClass:
                def method(self, value: int) -> str:
                    return str(value)
            """
        )
        tree = ast.parse(code)
        class_node = tree.body[0]
        assert isinstance(class_node, ast.ClassDef)
        method_node = class_node.body[0]
        assert isinstance(method_node, (ast.FunctionDef, ast.AsyncFunctionDef))

        extractor = ContractExtractor()
        contracts = extractor.extract_function_contracts(method_node)

        # self should be included in parameters but can be filtered if needed
        param_names = [p["name"] for p in contracts["parameters"]]
        assert "self" in param_names or len(param_names) == 1  # self might be filtered or included

    def test_extract_function_contracts_empty_function(self):
        """Test extracting contracts from empty function."""
        code = dedent(
            """
            def empty() -> None:
                pass
            """
        )
        tree = ast.parse(code)
        func_node = _get_function_node(tree)

        extractor = ContractExtractor()
        contracts = extractor.extract_function_contracts(func_node)

        assert isinstance(contracts, dict)
        assert len(contracts["parameters"]) == 0
        assert contracts["return_type"] is not None
        assert contracts["return_type"]["type"] in ("None", "NoneType", "null")

