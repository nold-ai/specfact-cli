"""Category group commands: project, backlog, code, spec, govern."""

from __future__ import annotations

from specfact_cli.groups.backlog_group import app as backlog_app
from specfact_cli.groups.codebase_group import app as codebase_app
from specfact_cli.groups.govern_group import app as govern_app
from specfact_cli.groups.project_group import app as project_app
from specfact_cli.groups.spec_group import app as spec_app


__all__ = [
    "backlog_app",
    "codebase_app",
    "govern_app",
    "project_app",
    "spec_app",
]
