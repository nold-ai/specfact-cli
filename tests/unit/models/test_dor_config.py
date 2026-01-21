"""
Unit tests for DefinitionOfReady (DoR) configuration model.

Tests DoR configuration loading, validation, and rule checking.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from beartype import beartype

from specfact_cli.models.dor_config import DefinitionOfReady


class TestDefinitionOfReady:
    """Test DefinitionOfReady model."""

    @beartype
    def test_create_dor_minimal(self) -> None:
        """Test creating DoR with minimal fields."""
        dor = DefinitionOfReady(rules={})

        assert dor.rules == {}
        assert dor.repo_path is None
        assert dor.team_id is None
        assert dor.project_id is None

    @beartype
    def test_create_dor_with_rules(self) -> None:
        """Test creating DoR with rules."""
        dor = DefinitionOfReady(
            rules={
                "story_points": True,
                "priority": True,
                "business_value": True,
                "acceptance_criteria": True,
            }
        )

        assert dor.rules["story_points"] is True
        assert dor.rules["priority"] is True
        assert dor.rules["business_value"] is True
        assert dor.rules["acceptance_criteria"] is True

    @beartype
    def test_validate_item_all_rules_satisfied(self) -> None:
        """Test validating item when all DoR rules are satisfied."""
        dor = DefinitionOfReady(
            rules={
                "story_points": True,
                "priority": True,
                "business_value": True,
                "acceptance_criteria": True,
            }
        )

        item_data = {
            "id": "123",
            "story_points": 5,
            "priority": "P1",
            "body_markdown": """## Business Value
This feature provides value to users.

## Acceptance Criteria
- User can do X
- User can do Y""",
        }

        errors = dor.validate_item(item_data)

        assert len(errors) == 0

    @beartype
    def test_validate_item_missing_story_points(self) -> None:
        """Test validating item when story points are missing."""
        dor = DefinitionOfReady(rules={"story_points": True})

        item_data = {"id": "123"}

        errors = dor.validate_item(item_data)

        assert len(errors) == 1
        assert "Missing story points" in errors[0]

    @beartype
    def test_validate_item_missing_business_value(self) -> None:
        """Test validating item when business value is missing."""
        dor = DefinitionOfReady(rules={"business_value": True})

        item_data = {"id": "123", "body_markdown": "Some content that does not mention value or benefit"}

        errors = dor.validate_item(item_data)

        assert len(errors) == 1
        assert "Missing business value" in errors[0]

    @beartype
    def test_validate_item_missing_acceptance_criteria(self) -> None:
        """Test validating item when acceptance criteria are missing."""
        dor = DefinitionOfReady(rules={"acceptance_criteria": True})

        item_data = {"id": "123", "body_markdown": "Some content that does not mention criteria or requirements"}

        errors = dor.validate_item(item_data)

        assert len(errors) == 1
        assert "Missing acceptance criteria" in errors[0]

    @beartype
    def test_validate_item_with_provider_fields(self) -> None:
        """Test validating item with fields in provider_fields."""
        dor = DefinitionOfReady(rules={"story_points": True, "priority": True})

        item_data = {
            "id": "123",
            "provider_fields": {"story_points": 8, "priority": "P2"},
        }

        errors = dor.validate_item(item_data)

        assert len(errors) == 0

    @beartype
    def test_load_from_file(self, tmp_path: Path) -> None:
        """Test loading DoR config from YAML file."""
        config_file = tmp_path / "dor.yaml"
        config_data = {
            "rules": {
                "story_points": True,
                "priority": True,
                "business_value": True,
            },
            "repo_path": str(tmp_path),
        }
        config_file.write_text(yaml.dump(config_data))

        dor = DefinitionOfReady.load_from_file(config_file)

        assert dor.rules["story_points"] is True
        assert dor.rules["priority"] is True
        assert dor.rules["business_value"] is True
        assert dor.repo_path == tmp_path

    @beartype
    def test_load_from_file_not_found(self) -> None:
        """Test loading non-existent DoR config file raises error."""
        non_existent = Path("/nonexistent/dor.yaml")

        with pytest.raises(FileNotFoundError):
            DefinitionOfReady.load_from_file(non_existent)

    @beartype
    def test_load_from_repo_found(self, tmp_path: Path) -> None:
        """Test loading DoR config from repository."""
        specfact_dir = tmp_path / ".specfact"
        specfact_dir.mkdir()
        config_file = specfact_dir / "dor.yaml"
        config_data = {"rules": {"story_points": True}}
        config_file.write_text(yaml.dump(config_data))

        dor = DefinitionOfReady.load_from_repo(tmp_path)

        assert dor is not None
        assert dor.rules["story_points"] is True

    @beartype
    def test_load_from_repo_not_found(self, tmp_path: Path) -> None:
        """Test loading DoR config when file doesn't exist returns None."""
        dor = DefinitionOfReady.load_from_repo(tmp_path)

        assert dor is None
