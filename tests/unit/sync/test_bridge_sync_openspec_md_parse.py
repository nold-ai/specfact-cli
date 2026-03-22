"""Tests for bridge_sync_openspec_md_parse."""

from __future__ import annotations

from specfact_cli.sync.bridge_sync_openspec_md_parse import bridge_sync_parse_openspec_proposal_markdown


def test_bridge_sync_parse_openspec_proposal_markdown_splits_sections() -> None:
    content = """# Change: Example Change

## Why
Rationale line.

## What Changes
Desc line one.

## Impact
Some impact.

## Source Tracking
- **GitHub Issue**: #1
"""
    title, rationale, description, impact = bridge_sync_parse_openspec_proposal_markdown(content)
    assert title == "Example Change"
    assert "Rationale" in rationale
    assert "Desc line" in description
    assert "Some impact" in impact
