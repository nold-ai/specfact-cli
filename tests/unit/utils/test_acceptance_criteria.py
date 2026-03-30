"""Unit tests for acceptance criteria helpers."""

from specfact_cli.utils.acceptance_criteria import is_code_specific_criteria


def test_is_code_specific_criteria_returns_false_for_control_character_input() -> None:
    """Pathological control-character strings should not raise during matching."""

    assert is_code_specific_criteria("\x02") is False
