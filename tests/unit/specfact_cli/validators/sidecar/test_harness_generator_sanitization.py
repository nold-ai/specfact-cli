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
        assert "/" not in harness or "harness_get_users_id" in harness

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
        assert "harness_get_users_id" in harness or "harness_get_users__id_" in harness
        assert "/" not in harness.split("def ")[1].split("(")[0] if "def " in harness else True
        assert "{" not in harness.split("def ")[1].split("(")[0] if "def " in harness else True

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
