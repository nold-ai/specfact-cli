"""Tests for codebase category group app (category-command-groups)."""

from __future__ import annotations

import os
from collections.abc import Generator
from unittest.mock import patch

import pytest

from specfact_cli.registry import CommandRegistry
from specfact_cli.registry.bootstrap import register_builtin_commands


@pytest.fixture(autouse=True)
def _clear_registry() -> Generator[None, None, None]:
    CommandRegistry._clear_for_testing()
    yield
    CommandRegistry._clear_for_testing()


def test_codebase_group_has_expected_subcommands() -> None:
    """Group app 'code' has expected sub-commands: analyze, drift, validate, repro."""
    with patch.dict(os.environ, {"SPECFACT_CATEGORY_GROUPING_ENABLED": "true"}, clear=False):
        register_builtin_commands()
    from typer.main import get_command

    from specfact_cli.registry.registry import CommandRegistry

    code_app = CommandRegistry.get_typer("code")
    click_code = get_command(code_app)
    assert hasattr(click_code, "commands")
    code_subcommands = list(click_code.commands.keys())
    for expected in ("analyze", "drift", "validate", "repro"):
        assert expected in code_subcommands, f"Expected sub-command {expected!r} in code group: {code_subcommands}"
