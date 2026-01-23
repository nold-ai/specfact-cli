"""
Unit tests for filter normalization functionality.

Tests the BacklogFilters.normalize_filter_value static method for
case-insensitive and whitespace-tolerant matching.
"""

from __future__ import annotations

from beartype import beartype

from specfact_cli.backlog.filters import BacklogFilters


class TestFilterNormalization:
    """Test filter normalization functionality."""

    @beartype
    def test_normalize_lowercase(self) -> None:
        """Test normalization of lowercase strings."""
        assert BacklogFilters.normalize_filter_value("open") == "open"
        assert BacklogFilters.normalize_filter_value("closed") == "closed"
        assert BacklogFilters.normalize_filter_value("johndoe") == "johndoe"

    @beartype
    def test_normalize_uppercase(self) -> None:
        """Test normalization of uppercase strings."""
        assert BacklogFilters.normalize_filter_value("OPEN") == "open"
        assert BacklogFilters.normalize_filter_value("CLOSED") == "closed"
        assert BacklogFilters.normalize_filter_value("JOHNDOE") == "johndoe"

    @beartype
    def test_normalize_mixed_case(self) -> None:
        """Test normalization of mixed case strings."""
        assert BacklogFilters.normalize_filter_value("Open") == "open"
        assert BacklogFilters.normalize_filter_value("ClOsEd") == "closed"
        assert BacklogFilters.normalize_filter_value("JohnDoe") == "johndoe"

    @beartype
    def test_normalize_with_whitespace(self) -> None:
        """Test normalization with leading/trailing whitespace."""
        assert BacklogFilters.normalize_filter_value("  open  ") == "open"
        assert BacklogFilters.normalize_filter_value("\tclosed\n") == "closed"
        assert BacklogFilters.normalize_filter_value("  jane doe  ") == "jane doe"

    @beartype
    def test_normalize_collapse_whitespace(self) -> None:
        """Test normalization collapses multiple whitespace characters."""
        assert BacklogFilters.normalize_filter_value("jane   doe") == "jane doe"
        assert BacklogFilters.normalize_filter_value("sprint   1") == "sprint 1"
        assert BacklogFilters.normalize_filter_value("new\t\tstate") == "new state"

    @beartype
    def test_normalize_none(self) -> None:
        """Test normalization of None values."""
        assert BacklogFilters.normalize_filter_value(None) is None

    @beartype
    def test_normalize_empty_string(self) -> None:
        """Test normalization of empty strings."""
        assert BacklogFilters.normalize_filter_value("") is None
        assert BacklogFilters.normalize_filter_value("   ") is None
        assert BacklogFilters.normalize_filter_value("\t\n") is None

    @beartype
    def test_normalize_real_world_examples(self) -> None:
        """Test normalization with real-world examples."""
        # State values
        assert BacklogFilters.normalize_filter_value("Active") == "active"
        assert BacklogFilters.normalize_filter_value("  New  ") == "new"
        assert BacklogFilters.normalize_filter_value("CLOSED") == "closed"

        # Assignee values
        assert BacklogFilters.normalize_filter_value("Jane Doe") == "jane doe"
        assert BacklogFilters.normalize_filter_value("  john.doe@example.com  ") == "john.doe@example.com"
        assert BacklogFilters.normalize_filter_value("JOHN   DOE") == "john doe"

        # Sprint values
        assert BacklogFilters.normalize_filter_value("Sprint 1") == "sprint 1"
        assert BacklogFilters.normalize_filter_value("  SPRINT   2  ") == "sprint 2"
        assert BacklogFilters.normalize_filter_value("Project\\Sprint 1") == "project\\sprint 1"

    @beartype
    def test_normalize_case_insensitive_matching(self) -> None:
        """Test that normalized values match regardless of case."""
        value1 = BacklogFilters.normalize_filter_value("Open")
        value2 = BacklogFilters.normalize_filter_value("OPEN")
        value3 = BacklogFilters.normalize_filter_value("open")
        value4 = BacklogFilters.normalize_filter_value("OpEn")

        assert value1 == value2 == value3 == value4 == "open"

    @beartype
    def test_normalize_whitespace_tolerant_matching(self) -> None:
        """Test that normalized values match regardless of whitespace."""
        value1 = BacklogFilters.normalize_filter_value("Jane Doe")
        value2 = BacklogFilters.normalize_filter_value("  Jane   Doe  ")
        value3 = BacklogFilters.normalize_filter_value("Jane\tDoe")
        value4 = BacklogFilters.normalize_filter_value("Jane\nDoe")

        assert value1 == value2 == value3 == value4 == "jane doe"
