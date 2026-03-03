"""Tests for backlog bridge converter implementations."""

from __future__ import annotations

from pathlib import Path

import pytest


pytest.importorskip("specfact_cli.modules.backlog.src.adapters.ado")
from specfact_cli.modules.backlog.src.adapters.ado import AdoConverter
from specfact_cli.modules.backlog.src.adapters.github import GitHubConverter
from specfact_cli.modules.backlog.src.adapters.jira import JiraConverter
from specfact_cli.modules.backlog.src.adapters.linear import LinearConverter


def test_converters_implement_schema_converter_contract() -> None:
    """All backlog converters should implement to_bundle/from_bundle."""
    converters = [AdoConverter(), JiraConverter(), LinearConverter(), GitHubConverter()]
    for converter in converters:
        assert callable(converter.to_bundle)
        assert callable(converter.from_bundle)


def test_ado_jira_linear_github_mapping_behavior() -> None:
    """Converters should map service-specific payloads to shared bundle fields."""
    ado_bundle = AdoConverter().to_bundle({"System.Id": 123, "System.Title": "ADO title"})
    jira_bundle = JiraConverter().to_bundle({"id": "JIRA-1", "fields": {"summary": "Jira title"}})
    linear_bundle = LinearConverter().to_bundle({"id": "LIN-1", "title": "Linear title"})
    github_bundle = GitHubConverter().to_bundle({"number": 77, "title": "GitHub title"})

    assert ado_bundle["id"] == 123
    assert jira_bundle["id"] == "JIRA-1"
    assert linear_bundle["id"] == "LIN-1"
    assert github_bundle["id"] == 77


def test_custom_mapping_override_loading(tmp_path: Path) -> None:
    """Custom mapping file should override default mapping when valid."""
    mapping_file = tmp_path / "github-bridge-mapping.yaml"
    mapping_file.write_text("to_bundle:\n  id: issue_number\n  title: subject\n", encoding="utf-8")

    converter = GitHubConverter(mapping_file=str(mapping_file))
    bundle = converter.to_bundle({"issue_number": 901, "subject": "Custom title"})

    assert bundle["id"] == 901
    assert bundle["title"] == "Custom title"


def test_converter_uses_default_mapping_without_mapping_file() -> None:
    """Converters should initialize and use defaults when no mapping file is provided."""
    converter = GitHubConverter()
    bundle = converter.to_bundle({"number": 42, "title": "Default mapping"})

    assert bundle["id"] == 42
    assert bundle["title"] == "Default mapping"
