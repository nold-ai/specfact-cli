"""Import robustness tests for policy module command shim."""

from __future__ import annotations


def test_policy_module_commands_importable_by_package_path() -> None:
    """Policy command shim SHALL be importable via fully-qualified package path."""
    from specfact_backlog.policy_engine.commands import app

    assert app is not None
