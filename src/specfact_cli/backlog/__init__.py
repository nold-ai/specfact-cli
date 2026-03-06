"""Shared backlog conversion helpers retained by core adapters."""

from __future__ import annotations

from specfact_cli.backlog.converter import (
    convert_ado_work_item_to_backlog_item,
    convert_github_issue_to_backlog_item,
)


__all__ = [
    "convert_ado_work_item_to_backlog_item",
    "convert_github_issue_to_backlog_item",
]
