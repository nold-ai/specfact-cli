"""Tests for project category group app ownership boundaries."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

import pytest
import typer
from typer.main import get_command

from specfact_cli.groups.project_group import build_app
from specfact_cli.registry import CommandRegistry


@pytest.fixture(autouse=True)
def _clear_registry() -> Generator[None, None, None]:
    CommandRegistry._clear_for_testing()
    yield
    CommandRegistry._clear_for_testing()


def test_project_group_excludes_code_owned_import_subcommand() -> None:
    """Project group keeps bundle lifecycle commands and excludes code-owned import."""
    member_app = typer.Typer()
    with patch.object(CommandRegistry, "get_module_typer", return_value=member_app):
        project_app = build_app()
    click_project = get_command(project_app)
    assert hasattr(click_project, "commands")
    project_subcommands = list(click_project.commands.keys())
    for expected in ("plan", "sync", "migrate"):
        assert expected in project_subcommands, (
            f"Expected sub-command {expected!r} in project group: {project_subcommands}"
        )
    assert getattr(project_app, "_specfact_flatten_same_name", None) == "project"
    assert "import" not in project_subcommands, (
        f"Code-first import should not remain on the project lifecycle surface: {project_subcommands}"
    )
