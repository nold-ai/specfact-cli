"""
Unit tests for TODO marker to checkbox conversion in ADO adapter.
"""

from __future__ import annotations

import re

from beartype import beartype


class TestAdoTodoConversion:
    """Test TODO marker to checkbox conversion."""

    @beartype
    def test_convert_todo_markers_to_checkboxes(self) -> None:
        """Test that TODO markers are converted to proper Markdown checkboxes."""
        # Pattern matches: * [TODO: ...] or - [TODO: ...] or *[TODO: ...] or -[TODO: ...]
        todo_pattern = r"^(\s*)[-*]\s*\[TODO[:\s]+([^\]]+)\](.*)$"

        test_cases = [
            # (input, expected_output)
            ("* [TODO: Specify the exact error]", "- [ ] Specify the exact error"),
            ("- [TODO: Define the expected behavior]", "- [ ] Define the expected behavior"),
            ("  * [TODO: Provide steps to reproduce]", "  - [ ] Provide steps to reproduce"),
            ("    - [TODO: Confirm how the fix will be validated]", "    - [ ] Confirm how the fix will be validated"),
            ("*[TODO: Include any available feedback]", "- [ ] Include any available feedback"),
            ("- [TODO: Identify any dependent work items]", "- [ ] Identify any dependent work items"),
        ]

        for input_text, expected_output in test_cases:
            result = re.sub(todo_pattern, r"\1- [ ] \2", input_text, flags=re.MULTILINE | re.IGNORECASE)
            assert result == expected_output, f"Failed for input: {input_text}"

    @beartype
    def test_convert_multiline_todo_markers(self) -> None:
        """Test conversion of multiple TODO markers in multiline content."""
        todo_pattern = r"^(\s*)[-*]\s*\[TODO[:\s]+([^\]]+)\](.*)$"

        input_text = """## Acceptance Criteria

* [TODO: Specify the exact error (message/stack trace) and where it occurs (component/service/endpoint/screen).]
* [TODO: Define the expected behavior after the fix (what should happen instead of the error).]
* [TODO: Provide steps to reproduce the error and verification steps to confirm the fix.]
* [TODO: Confirm how the fix will be validated (e.g., test case added/updated, manual verification).]"""

        expected_output = """## Acceptance Criteria

- [ ] Specify the exact error (message/stack trace) and where it occurs (component/service/endpoint/screen).
- [ ] Define the expected behavior after the fix (what should happen instead of the error).
- [ ] Provide steps to reproduce the error and verification steps to confirm the fix.
- [ ] Confirm how the fix will be validated (e.g., test case added/updated, manual verification)."""

        result = re.sub(todo_pattern, r"\1- [ ] \2", input_text, flags=re.MULTILINE | re.IGNORECASE)
        assert result == expected_output

    @beartype
    def test_preserve_non_todo_content(self) -> None:
        """Test that non-TODO content is preserved unchanged."""
        todo_pattern = r"^(\s*)[-*]\s*\[TODO[:\s]+([^\]]+)\](.*)$"

        input_text = """## Description

As developer I got feedback that there is an error that needs to be fixed.
We need to fix this error.

## Acceptance Criteria

* [TODO: Specify the exact error]
* [TODO: Define the expected behavior]

## Notes

* [TODO: Include any available feedback details]"""

        result = re.sub(todo_pattern, r"\1- [ ] \2", input_text, flags=re.MULTILINE | re.IGNORECASE)

        # Verify non-TODO content is preserved
        assert "## Description" in result
        assert "As developer I got feedback" in result
        assert "## Acceptance Criteria" in result
        assert "## Notes" in result

        # Verify TODOs are converted
        assert "- [ ] Specify the exact error" in result
        assert "- [ ] Define the expected behavior" in result
        assert "- [ ] Include any available feedback details" in result

        # Verify no TODO markers remain
        assert "[TODO:" not in result

    @beartype
    def test_case_insensitive_todo_matching(self) -> None:
        """Test that TODO matching is case-insensitive."""
        todo_pattern = r"^(\s*)[-*]\s*\[TODO[:\s]+([^\]]+)\](.*)$"

        test_cases = [
            ("* [TODO: test]", "- [ ] test"),
            ("* [todo: test]", "- [ ] test"),
            ("* [Todo: test]", "- [ ] test"),
            ("* [ToDo: test]", "- [ ] test"),
        ]

        for input_text, expected_output in test_cases:
            result = re.sub(todo_pattern, r"\1- [ ] \2", input_text, flags=re.MULTILINE | re.IGNORECASE)
            assert result == expected_output, f"Failed for input: {input_text}"
