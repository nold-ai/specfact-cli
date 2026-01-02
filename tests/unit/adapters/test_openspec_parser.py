"""Unit tests for OpenSpec parser."""

from __future__ import annotations

from pathlib import Path

import pytest

from specfact_cli.adapters.openspec_parser import OpenSpecParser


@pytest.fixture
def parser() -> OpenSpecParser:
    """Create OpenSpec parser instance for testing."""
    return OpenSpecParser()


@pytest.fixture
def openspec_repo(tmp_path: Path) -> Path:
    """Create a temporary OpenSpec repository structure."""
    openspec_dir = tmp_path / "openspec"
    openspec_dir.mkdir()
    (openspec_dir / "project.md").write_text(
        """# Project

## Purpose
Test project for OpenSpec integration.

## Context
This is a test project.
"""
    )
    specs_dir = openspec_dir / "specs"
    specs_dir.mkdir()
    feature_dir = specs_dir / "001-auth"
    feature_dir.mkdir()
    (feature_dir / "spec.md").write_text(
        """# Authentication Feature

## Overview
User authentication system.

## Requirements
- Login functionality
- Password reset
"""
    )
    changes_dir = openspec_dir / "changes"
    changes_dir.mkdir()
    change_dir = changes_dir / "add-feature-x"
    change_dir.mkdir()
    (change_dir / "proposal.md").write_text(
        """# Change Proposal: Add Feature X

## Summary
Add new feature X to the system.

## Rationale
Feature X is needed for...
"""
    )
    return tmp_path


class TestOpenSpecParser:
    """Test OpenSpec parser implementation."""

    def test_parse_project_md_valid(self, parser: OpenSpecParser, openspec_repo: Path) -> None:
        """Test parsing valid project.md file."""
        project_path = openspec_repo / "openspec" / "project.md"
        parsed = parser.parse_project_md(project_path)

        assert parsed is not None
        assert "purpose" in parsed
        assert "context" in parsed
        assert parsed["purpose"] == ["Test project for OpenSpec integration."]

    def test_parse_project_md_missing(self, parser: OpenSpecParser, tmp_path: Path) -> None:
        """Test parsing missing project.md file."""
        project_path = tmp_path / "nonexistent" / "project.md"
        parsed = parser.parse_project_md(project_path)

        assert parsed is None

    def test_parse_spec_md_valid(self, parser: OpenSpecParser, openspec_repo: Path) -> None:
        """Test parsing valid spec.md file."""
        spec_path = openspec_repo / "openspec" / "specs" / "001-auth" / "spec.md"
        parsed = parser.parse_spec_md(spec_path)

        assert parsed is not None
        assert "overview" in parsed
        assert "requirements" in parsed
        assert "Authentication Feature" in parsed.get("raw_content", "")

    def test_parse_spec_md_missing(self, parser: OpenSpecParser, tmp_path: Path) -> None:
        """Test parsing missing spec.md file."""
        spec_path = tmp_path / "nonexistent" / "spec.md"
        parsed = parser.parse_spec_md(spec_path)

        assert parsed is None

    def test_parse_change_proposal_valid(self, parser: OpenSpecParser, openspec_repo: Path) -> None:
        """Test parsing valid change proposal."""
        proposal_path = openspec_repo / "openspec" / "changes" / "add-feature-x" / "proposal.md"
        parsed = parser.parse_change_proposal(proposal_path)

        assert parsed is not None
        assert "summary" in parsed
        assert "rationale" in parsed
        assert "Add Feature X" in parsed.get("raw_content", "")

    def test_parse_change_proposal_missing(self, parser: OpenSpecParser, tmp_path: Path) -> None:
        """Test parsing missing change proposal."""
        proposal_path = tmp_path / "nonexistent" / "proposal.md"
        parsed = parser.parse_change_proposal(proposal_path)

        assert parsed is None

    def test_parse_change_spec_delta_added(self, parser: OpenSpecParser, tmp_path: Path) -> None:
        """Test parsing change spec delta with ADDED type."""
        delta_path = tmp_path / "delta.md"
        delta_path.write_text(
            """# Change Spec Delta

## Type
ADDED

## Feature ID
002-payment

## Content
New payment feature specification.
"""
        )
        parsed = parser.parse_change_spec_delta(delta_path)

        assert parsed is not None
        assert parsed.get("type") == "ADDED"
        assert parsed.get("feature_id") == "002-payment"

    def test_parse_change_spec_delta_modified(self, parser: OpenSpecParser, tmp_path: Path) -> None:
        """Test parsing change spec delta with MODIFIED type."""
        delta_path = tmp_path / "delta.md"
        delta_path.write_text(
            """# Change Spec Delta

## Type
MODIFIED

## Feature ID
001-auth

## Content
Updated authentication feature.
"""
        )
        parsed = parser.parse_change_spec_delta(delta_path)

        assert parsed is not None
        assert parsed.get("type") == "MODIFIED"
        assert parsed.get("feature_id") == "001-auth"

    def test_parse_change_spec_delta_removed(self, parser: OpenSpecParser, tmp_path: Path) -> None:
        """Test parsing change spec delta with REMOVED type."""
        delta_path = tmp_path / "delta.md"
        delta_path.write_text(
            """# Change Spec Delta

## Type
REMOVED

## Feature ID
003-old-feature
"""
        )
        parsed = parser.parse_change_spec_delta(delta_path)

        assert parsed is not None
        assert parsed.get("type") == "REMOVED"
        assert parsed.get("feature_id") == "003-old-feature"

    def test_list_active_changes(self, parser: OpenSpecParser, openspec_repo: Path) -> None:
        """Test listing active changes."""
        # list_active_changes expects base_path (repo root), not changes_dir
        active_changes = parser.list_active_changes(openspec_repo)

        assert len(active_changes) >= 1
        assert any("add-feature-x" in str(change) for change in active_changes)

    def test_list_active_changes_empty(self, parser: OpenSpecParser, tmp_path: Path) -> None:
        """Test listing active changes when directory is empty."""
        changes_dir = tmp_path / "changes"
        changes_dir.mkdir()
        active_changes = parser.list_active_changes(changes_dir)

        assert len(active_changes) == 0

    def test_list_active_changes_nonexistent(self, parser: OpenSpecParser, tmp_path: Path) -> None:
        """Test listing active changes when directory doesn't exist."""
        changes_dir = tmp_path / "nonexistent" / "changes"
        active_changes = parser.list_active_changes(changes_dir)

        assert len(active_changes) == 0
