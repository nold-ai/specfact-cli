"""Tests for codebase category group app (category-command-groups)."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

import pytest
import typer
from typer.main import get_command

from specfact_cli.groups.codebase_group import build_app
from specfact_cli.registry import CommandRegistry


@pytest.fixture(autouse=True)
def _clear_registry() -> Generator[None, None, None]:
    CommandRegistry._clear_for_testing()
    yield
    CommandRegistry._clear_for_testing()


def test_codebase_group_has_expected_subcommands() -> None:
    """Group app 'code' exposes expected subcommands when bundle members are available."""
    member_app = typer.Typer()
    with patch.object(CommandRegistry, "get_module_typer", return_value=member_app):
        code_app = build_app()
    click_code = get_command(code_app)
    assert hasattr(click_code, "commands")
    code_subcommands = list(click_code.commands.keys())
    for expected in ("analyze", "drift", "validate", "repro", "import"):
        assert expected in code_subcommands, f"Expected sub-command {expected!r} in code group: {code_subcommands}"
