"""
Unit tests for OpenAPITestConverter.

Tests the conversion of test patterns to OpenAPI examples using Semgrep and AST.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from specfact_cli.generators.test_to_openapi import OpenAPITestConverter


class TestOpenAPITestConverterClass:
    """Tests for OpenAPITestConverter."""

    def test_init(self, tmp_path: Path) -> None:
        """Test converter initialization."""
        converter = OpenAPITestConverter(tmp_path)
        assert converter.repo_path == tmp_path.resolve()

    def test_init_with_custom_config(self, tmp_path: Path) -> None:
        """Warn when a caller requests a retired test-pattern config."""
        custom_config = tmp_path / "custom-test-patterns.yml"
        with pytest.warns(UserWarning, match="extracts examples from Python test source"):
            OpenAPITestConverter(tmp_path, semgrep_config=custom_config)

    def test_extract_examples_from_tests_empty_list(self, tmp_path: Path) -> None:
        """Test extracting examples from empty test file list."""
        converter = OpenAPITestConverter(tmp_path)
        examples = converter.extract_examples_from_tests([])
        assert examples == {}

    def test_extract_examples_from_tests_nonexistent_file(self, tmp_path: Path) -> None:
        """Test extracting examples from non-existent test file."""
        converter = OpenAPITestConverter(tmp_path)
        examples = converter.extract_examples_from_tests(["nonexistent_test.py"])
        assert examples == {}

    def test_extract_examples_from_ast_simple_test(self, tmp_path: Path) -> None:
        """Test AST-based extraction from a simple test file."""
        # Create a test file
        test_file = tmp_path / "test_example.py"
        test_file.write_text(
            '''
def test_create_user():
    """Test creating a user."""
    response = client.post("/api/users", json={"name": "John", "email": "john@example.com"})
    assert response.status_code == 201
    assert response.json() == {"id": 1, "name": "John", "email": "john@example.com"}
'''
        )

        converter = OpenAPITestConverter(tmp_path)
        # Use extract_examples_from_tests which is the public API
        examples = converter.extract_examples_from_tests(["test_example.py::test_create_user"])

        assert examples == {
            "post_api_users": {
                "operation_id": "post_api_users",
                "request": {
                    "path": "/api/users",
                    "method": "POST",
                    "body": {"name": "John", "email": "john@example.com"},
                },
                "response": {"id": 1, "name": "John", "email": "john@example.com"},
                "status_code": 201,
            }
        }

    def test_extract_ast_value_constant(self, tmp_path: Path) -> None:
        """Test extracting value from AST Constant node."""
        import ast

        converter = OpenAPITestConverter(tmp_path)
        node = ast.Constant(value="test")
        result = converter._extract_ast_value(node)
        assert result == "test"

    def test_extract_ast_value_dict(self, tmp_path: Path) -> None:
        """Test extracting value from AST Dict node."""
        import ast

        converter = OpenAPITestConverter(tmp_path)
        node = ast.Dict(
            keys=[ast.Constant(value="key1"), ast.Constant(value="key2")],
            values=[ast.Constant(value="value1"), ast.Constant(value="value2")],
        )
        result = converter._extract_ast_value(node)
        assert isinstance(result, dict)
        assert result["key1"] == "value1"
        assert result["key2"] == "value2"

    def test_extract_ast_value_list(self, tmp_path: Path) -> None:
        """Test extracting value from AST List node."""
        import ast

        converter = OpenAPITestConverter(tmp_path)
        node = ast.List(elts=[ast.Constant(value=1), ast.Constant(value=2), ast.Constant(value=3)])
        result = converter._extract_ast_value(node)
        assert result == [1, 2, 3]

    def test_extract_string_arg(self, tmp_path: Path) -> None:
        """Test extracting string argument from function call."""
        import ast

        converter = OpenAPITestConverter(tmp_path)
        call = ast.Call(
            func=ast.Name(id="post"),
            args=[ast.Constant(value="/api/users")],
            keywords=[],
        )
        result = converter._extract_string_arg(call, 0)
        assert result == "/api/users"

    def test_extract_json_arg(self, tmp_path: Path) -> None:
        """Test extracting JSON argument from function call."""
        import ast

        converter = OpenAPITestConverter(tmp_path)
        call = ast.Call(
            func=ast.Name(id="post"),
            args=[],
            keywords=[
                ast.keyword(
                    arg="json",
                    value=ast.Dict(
                        keys=[ast.Constant(value="name")],
                        values=[ast.Constant(value="John")],
                    ),
                )
            ],
        )
        result = converter._extract_json_arg(call, "json")
        assert result == {"name": "John"}

    def test_extract_examples_from_tests_parallel_processing(self, tmp_path: Path) -> None:
        """Retain examples across the selected files."""
        # Create multiple test files
        test_files = []
        for i in range(5):
            test_file = tmp_path / f"test_api_{i}.py"
            test_file.write_text(
                f'''
def test_create_user_{i}():
    """Test creating a user {i}."""
    response = client.post("/api/users/{i}", json={{"name": "User{i}", "email": "user{i}@example.com"}})
    assert response.status_code == 201
'''
            )
            test_files.append(f"test_api_{i}.py")

        converter = OpenAPITestConverter(tmp_path)
        examples = converter.extract_examples_from_tests(test_files)

        assert set(examples) == {f"post_api_users_{i}" for i in range(5)}
        assert all(example["status_code"] == 201 for example in examples.values())

    def test_extract_examples_from_tests_limits_to_10_files(self, tmp_path: Path) -> None:
        """Retain the source path's coverage for more than ten selected files."""
        # Create 15 test files
        test_files = []
        for i in range(15):
            test_file = tmp_path / f"test_api_{i}.py"
            test_file.write_text(
                f'''
def test_create_user_{i}():
    """Test creating a user {i}."""
    response = client.post("/api/users/{i}", json={{"name": "User{i}"}})
    assert response.status_code == 201
'''
            )
            test_files.append(f"test_api_{i}.py")

        converter = OpenAPITestConverter(tmp_path)
        examples = converter.extract_examples_from_tests(test_files)

        assert len(examples) == 15

    def test_only_selected_tests_contribute_to_examples(self, tmp_path: Path) -> None:
        """Keep selection and the response variable bound to the HTTP operation."""
        test_file = tmp_path / "test_api.py"
        test_file.write_text(
            """
def test_create_user():
    response = client.post("/api/users", json={"name": "John"})
    assert response.status_code == 201
    assert unrelated.status_code == 404
    assert response.json() == {}

def test_read_user():
    response = client.get("/api/users/1")
    assert response.status_code == 200
"""
        )

        converter = OpenAPITestConverter(tmp_path)

        examples = converter.extract_examples_from_tests(["test_api.py::test_create_user"])
        assert set(examples) == {"post_api_users"}
        assert examples["post_api_users"]["status_code"] == 201
        assert examples["post_api_users"]["response"] == {}
