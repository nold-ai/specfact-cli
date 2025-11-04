"""Unit tests for interactive prompt utilities.

Focus: Business logic and edge cases only (@beartype handles type validation).
"""

from unittest.mock import patch

from specfact_cli.utils.prompts import (
    display_summary,
    print_error,
    print_info,
    print_section,
    print_success,
    print_warning,
    prompt_confirm,
    prompt_dict,
    prompt_list,
    prompt_text,
)


class TestPromptText:
    """Test prompt_text function."""

    @patch("specfact_cli.utils.prompts.Prompt.ask")
    def test_prompt_text_with_value(self, mock_ask):
        """Test prompt_text returns user input."""
        mock_ask.return_value = "Test Value"
        result = prompt_text("Enter value")
        assert result == "Test Value"
        mock_ask.assert_called_once_with("Enter value", default="")

    @patch("specfact_cli.utils.prompts.Prompt.ask")
    def test_prompt_text_with_default(self, mock_ask):
        """Test prompt_text with default value."""
        mock_ask.return_value = "default_value"
        result = prompt_text("Enter value", default="default_value")
        assert result == "default_value"
        mock_ask.assert_called_once_with("Enter value", default="default_value")

    @patch("specfact_cli.utils.prompts.Prompt.ask")
    @patch("specfact_cli.utils.prompts.console.print")
    def test_prompt_text_required_retry(self, mock_print, mock_ask):
        """Test prompt_text retries when required and empty."""
        mock_ask.side_effect = ["", "", "Final Value"]
        result = prompt_text("Enter value", required=True)
        assert result == "Final Value"
        assert mock_ask.call_count == 3
        assert mock_print.call_count == 2  # Two warnings for empty input

    @patch("specfact_cli.utils.prompts.Prompt.ask")
    def test_prompt_text_not_required(self, mock_ask):
        """Test prompt_text allows empty when not required."""
        mock_ask.return_value = ""
        result = prompt_text("Enter value", required=False)
        assert result == ""
        mock_ask.assert_called_once()


class TestPromptList:
    """Test prompt_list function."""

    @patch("specfact_cli.utils.prompts.Prompt.ask")
    def test_prompt_list_basic(self, mock_ask):
        """Test prompt_list parses comma-separated values."""
        mock_ask.return_value = "item1, item2, item3"
        result = prompt_list("Enter items")
        assert result == ["item1", "item2", "item3"]

    @patch("specfact_cli.utils.prompts.Prompt.ask")
    def test_prompt_list_with_spaces(self, mock_ask):
        """Test prompt_list strips whitespace."""
        mock_ask.return_value = "  item1  ,  item2  ,  item3  "
        result = prompt_list("Enter items")
        assert result == ["item1", "item2", "item3"]

    @patch("specfact_cli.utils.prompts.Prompt.ask")
    def test_prompt_list_empty(self, mock_ask):
        """Test prompt_list returns empty list for empty input."""
        mock_ask.return_value = ""
        result = prompt_list("Enter items")
        assert result == []

    @patch("specfact_cli.utils.prompts.Prompt.ask")
    def test_prompt_list_custom_separator(self, mock_ask):
        """Test prompt_list with custom separator."""
        mock_ask.return_value = "item1;item2;item3"
        result = prompt_list("Enter items", separator=";")
        assert result == ["item1", "item2", "item3"]

    @patch("specfact_cli.utils.prompts.Prompt.ask")
    def test_prompt_list_filters_empty_items(self, mock_ask):
        """Test prompt_list filters out empty items."""
        mock_ask.return_value = "item1, , item2, , item3"
        result = prompt_list("Enter items")
        assert result == ["item1", "item2", "item3"]


class TestPromptDict:
    """Test prompt_dict function."""

    @patch("specfact_cli.utils.prompts.Prompt.ask")
    @patch("specfact_cli.utils.prompts.console.print")
    def test_prompt_dict_basic(self, mock_print, mock_ask):
        """Test prompt_dict parses key:value pairs."""
        mock_ask.side_effect = ["key1:value1", "key2:value2", ""]
        result = prompt_dict("Enter pairs")
        assert result == {"key1": "value1", "key2": "value2"}

    @patch("specfact_cli.utils.prompts.Prompt.ask")
    @patch("specfact_cli.utils.prompts.console.print")
    def test_prompt_dict_with_numbers(self, mock_print, mock_ask):
        """Test prompt_dict converts numbers automatically."""
        mock_ask.side_effect = ["count:42", "rate:3.14", "name:test", ""]
        result = prompt_dict("Enter pairs")
        assert result == {"count": 42, "rate": 3.14, "name": "test"}
        assert isinstance(result["count"], int)
        assert isinstance(result["rate"], float)
        assert isinstance(result["name"], str)

    @patch("specfact_cli.utils.prompts.Prompt.ask")
    @patch("specfact_cli.utils.prompts.console.print")
    def test_prompt_dict_strips_whitespace(self, mock_print, mock_ask):
        """Test prompt_dict strips whitespace from keys and values."""
        mock_ask.side_effect = ["  key1  :  value1  ", ""]
        result = prompt_dict("Enter pairs")
        assert result == {"key1": "value1"}

    @patch("specfact_cli.utils.prompts.Prompt.ask")
    @patch("specfact_cli.utils.prompts.console.print")
    def test_prompt_dict_invalid_format_retry(self, mock_print, mock_ask):
        """Test prompt_dict handles invalid format and retries."""
        mock_ask.side_effect = ["invalid", "key:value", ""]
        result = prompt_dict("Enter pairs")
        assert result == {"key": "value"}
        # Should print warning for invalid format
        assert any("Format should be key:value" in str(call) for call in mock_print.call_args_list)

    @patch("specfact_cli.utils.prompts.Prompt.ask")
    @patch("specfact_cli.utils.prompts.console.print")
    def test_prompt_dict_empty(self, mock_print, mock_ask):
        """Test prompt_dict returns empty dict when no input."""
        mock_ask.return_value = ""
        result = prompt_dict("Enter pairs")
        assert result == {}

    @patch("specfact_cli.utils.prompts.Prompt.ask")
    @patch("specfact_cli.utils.prompts.console.print")
    def test_prompt_dict_colon_in_value(self, mock_print, mock_ask):
        """Test prompt_dict handles colons in values."""
        mock_ask.side_effect = ["url:https://example.com:8080", ""]
        result = prompt_dict("Enter pairs")
        assert result == {"url": "https://example.com:8080"}


class TestPromptConfirm:
    """Test prompt_confirm function."""

    @patch("specfact_cli.utils.prompts.Confirm.ask")
    def test_prompt_confirm_true(self, mock_ask):
        """Test prompt_confirm returns True."""
        mock_ask.return_value = True
        result = prompt_confirm("Confirm?")
        assert result is True
        mock_ask.assert_called_once_with("Confirm?", default=False)

    @patch("specfact_cli.utils.prompts.Confirm.ask")
    def test_prompt_confirm_false(self, mock_ask):
        """Test prompt_confirm returns False."""
        mock_ask.return_value = False
        result = prompt_confirm("Confirm?")
        assert result is False

    @patch("specfact_cli.utils.prompts.Confirm.ask")
    def test_prompt_confirm_with_default_true(self, mock_ask):
        """Test prompt_confirm with default True."""
        mock_ask.return_value = True
        result = prompt_confirm("Confirm?", default=True)
        assert result is True
        mock_ask.assert_called_once_with("Confirm?", default=True)


class TestDisplaySummary:
    """Test display_summary function."""

    @patch("specfact_cli.utils.prompts.console.print")
    def test_display_summary_basic(self, mock_print):
        """Test display_summary with basic data."""
        data = {"key1": "value1", "key2": "value2"}
        display_summary("Test Summary", data)
        mock_print.assert_called_once()

    @patch("specfact_cli.utils.prompts.console.print")
    def test_display_summary_with_list(self, mock_print):
        """Test display_summary with list values."""
        data = {"items": ["item1", "item2", "item3"]}
        display_summary("Test Summary", data)
        mock_print.assert_called_once()

    @patch("specfact_cli.utils.prompts.console.print")
    def test_display_summary_with_dict(self, mock_print):
        """Test display_summary with dict values."""
        data = {"config": {"key1": "value1", "key2": "value2"}}
        display_summary("Test Summary", data)
        mock_print.assert_called_once()

    @patch("specfact_cli.utils.prompts.console.print")
    def test_display_summary_empty(self, mock_print):
        """Test display_summary with empty data."""
        data = {}
        display_summary("Test Summary", data)
        mock_print.assert_called_once()


class TestPrintHelpers:
    """Test print helper functions."""

    @patch("specfact_cli.utils.prompts.console.print")
    def test_print_success(self, mock_print):
        """Test print_success function."""
        print_success("Success message")
        mock_print.assert_called_once()
        call_args = str(mock_print.call_args)
        assert "Success message" in call_args
        assert "✅" in call_args or "green" in call_args

    @patch("specfact_cli.utils.prompts.console.print")
    def test_print_error(self, mock_print):
        """Test print_error function."""
        print_error("Error message")
        mock_print.assert_called_once()
        call_args = str(mock_print.call_args)
        assert "Error message" in call_args
        assert "❌" in call_args or "red" in call_args

    @patch("specfact_cli.utils.prompts.console.print")
    def test_print_warning(self, mock_print):
        """Test print_warning function."""
        print_warning("Warning message")
        mock_print.assert_called_once()
        call_args = str(mock_print.call_args)
        assert "Warning message" in call_args
        assert "⚠️" in call_args or "yellow" in call_args

    @patch("specfact_cli.utils.prompts.console.print")
    def test_print_info(self, mock_print):
        """Test print_info function."""
        print_info("Info message")
        mock_print.assert_called_once()
        call_args = str(mock_print.call_args)
        assert "Info message" in call_args
        assert "ℹ️" in call_args or "blue" in call_args

    @patch("specfact_cli.utils.prompts.console.print")
    def test_print_section(self, mock_print):
        """Test print_section function."""
        print_section("Section Title")
        # Should print 3 times: separator, title, separator
        assert mock_print.call_count == 3
        call_args = [str(call) for call in mock_print.call_args_list]
        # Check that title appears in calls
        assert any("Section Title" in arg for arg in call_args)
