"""
Unit tests for harness generator function name sanitization.
"""

from __future__ import annotations

from specfact_cli.validators.sidecar.harness_generator import render_harness


class TestHarnessGeneratorSanitization:
    """Test function name sanitization in harness generation."""

    def test_sanitize_path_with_slashes(self) -> None:
        """Test that path characters like / are sanitized."""
        operations = [
            {
                "operation_id": "get_users_id",
                "path": "/users/{id}",
                "method": "GET",
                "request_schema": {},
                "response_schema": {},
            }
        ]

        harness = render_harness(operations)

        # Should contain valid Python function name
        assert "def harness_" in harness
        # Extract function name and verify it's valid
        for line in harness.split("\n"):
            if line.strip().startswith("def harness_"):
                func_name = line.split("def ")[1].split("(")[0]
                assert all(c.isalnum() or c == "_" for c in func_name), f"Invalid function name: {func_name}"
                break

    def test_sanitize_operation_id_with_special_chars(self) -> None:
        """Test that operation IDs with special characters are sanitized."""
        operations = [
            {
                "operation_id": "get/users/{id}",
                "path": "/users/{id}",
                "method": "GET",
                "request_schema": {},
                "response_schema": {},
            }
        ]

        harness = render_harness(operations)

        # Should replace /, {, } with underscores
        # The sanitized function name should be harness_get_users__id_ (all special chars become _)
        assert "def harness_" in harness
        # Extract function name from the def line
        for line in harness.split("\n"):
            if line.strip().startswith("def harness_"):
                func_name = line.split("def ")[1].split("(")[0]
                # Should not contain invalid characters
                assert "/" not in func_name, f"Function name contains /: {func_name}"
                assert "{" not in func_name, f"Function name contains {{: {func_name}"
                assert "}" not in func_name, f"Function name contains }}: {func_name}"
                # Should only contain valid identifier characters
                assert all(c.isalnum() or c == "_" for c in func_name), f"Invalid function name: {func_name}"
                break

    def test_sanitize_fallback_operation_id(self) -> None:
        """Test that fallback operation IDs (method_path) are sanitized."""
        operations = [
            {
                "operation_id": "GET_/users/{id}",
                "path": "/users/{id}",
                "method": "GET",
                "request_schema": {},
                "response_schema": {},
            }
        ]

        harness = render_harness(operations)

        # Should create valid function name
        assert "def harness_" in harness
        # Should not contain invalid characters in function name
        lines = harness.split("\n")
        for line in lines:
            if line.strip().startswith("def harness_"):
                func_name = line.split("def ")[1].split("(")[0]
                assert all(c.isalnum() or c == "_" for c in func_name), f"Invalid function name: {func_name}"
