"""Unit tests for optional dependency helpers."""

from specfact_cli.utils.optional_deps import check_python_package_available


def test_check_python_package_available_returns_false_for_control_character_name() -> None:
    """Control-character package names should fail closed instead of raising."""

    assert check_python_package_available("\x00") is False
