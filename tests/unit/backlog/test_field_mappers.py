"""
Unit tests for field mapper classes.

Tests for FieldMapper base class, GitHubFieldMapper, and AdoFieldMapper.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from specfact_cli.backlog.mappers.ado_mapper import AdoFieldMapper
from specfact_cli.backlog.mappers.base import FieldMapper
from specfact_cli.backlog.mappers.github_mapper import GitHubFieldMapper


class TestFieldMapperBase:
    """Tests for FieldMapper abstract base class."""

    def test_canonical_fields_defined(self) -> None:
        """Test that canonical fields are properly defined."""
        expected_fields = {
            "description",
            "acceptance_criteria",
            "story_points",
            "business_value",
            "priority",
            "value_points",
            "work_item_type",
        }
        assert expected_fields == FieldMapper.CANONICAL_FIELDS

    def test_is_canonical_field(self) -> None:
        """Test is_canonical_field method."""

        # Create a concrete implementation for testing
        class ConcreteMapper(FieldMapper):
            def extract_fields(self, item_data: dict) -> dict:
                return {}

            def map_from_canonical(self, canonical_fields: dict) -> dict:
                return {}

        mapper = ConcreteMapper()

        # Test canonical fields
        assert mapper.is_canonical_field("description") is True
        assert mapper.is_canonical_field("story_points") is True
        assert mapper.is_canonical_field("business_value") is True
        assert mapper.is_canonical_field("priority") is True
        assert mapper.is_canonical_field("acceptance_criteria") is True
        assert mapper.is_canonical_field("value_points") is True
        assert mapper.is_canonical_field("work_item_type") is True

        # Test non-canonical fields
        assert mapper.is_canonical_field("title") is False
        assert mapper.is_canonical_field("body") is False
        assert mapper.is_canonical_field("invalid_field") is False


class TestGitHubFieldMapper:
    """Tests for GitHubFieldMapper."""

    def test_extract_description_from_default_content(self) -> None:
        """Test extracting description from default body content."""
        mapper = GitHubFieldMapper()
        item_data = {
            "body": "This is the main description content.\n\nSome additional text.",
            "labels": [],
        }
        fields = mapper.extract_fields(item_data)
        assert "description" in fields
        assert "This is the main description content" in fields["description"]

    def test_extract_description_from_section(self) -> None:
        """Test extracting description from ## Description section."""
        mapper = GitHubFieldMapper()
        item_data = {
            "body": "## Description\n\nThis is the description section.\n\n## Other Section\n\nOther content.",
            "labels": [],
        }
        fields = mapper.extract_fields(item_data)
        assert "description" in fields
        assert "This is the description section" in fields["description"]

    def test_extract_acceptance_criteria(self) -> None:
        """Test extracting acceptance criteria from ## Acceptance Criteria heading."""
        mapper = GitHubFieldMapper()
        item_data = {
            "body": "## Description\n\nMain content.\n\n## Acceptance Criteria\n\n- Criterion 1\n- Criterion 2",
            "labels": [],
        }
        fields = mapper.extract_fields(item_data)
        assert "acceptance_criteria" in fields
        assert "Criterion 1" in fields["acceptance_criteria"]
        assert "Criterion 2" in fields["acceptance_criteria"]

    def test_extract_story_points_from_heading(self) -> None:
        """Test extracting story points from ## Story Points heading."""
        mapper = GitHubFieldMapper()
        item_data = {
            "body": "## Story Points\n\n8",
            "labels": [],
        }
        fields = mapper.extract_fields(item_data)
        assert fields["story_points"] == 8

    def test_extract_story_points_from_bold_pattern(self) -> None:
        """Test extracting story points from **Story Points:** pattern."""
        mapper = GitHubFieldMapper()
        item_data = {
            "body": "**Story Points:** 13",
            "labels": [],
        }
        fields = mapper.extract_fields(item_data)
        assert fields["story_points"] == 13

    def test_extract_business_value(self) -> None:
        """Test extracting business value."""
        mapper = GitHubFieldMapper()
        item_data = {
            "body": "## Business Value\n\n75",
            "labels": [],
        }
        fields = mapper.extract_fields(item_data)
        assert fields["business_value"] == 75

    def test_extract_priority(self) -> None:
        """Test extracting priority."""
        mapper = GitHubFieldMapper()
        item_data = {
            "body": "## Priority\n\n2",
            "labels": [],
        }
        fields = mapper.extract_fields(item_data)
        assert fields["priority"] == 2

    def test_calculate_value_points(self) -> None:
        """Test calculating value points from business_value / story_points."""
        mapper = GitHubFieldMapper()
        item_data = {
            "body": "## Story Points\n\n5\n\n## Business Value\n\n25",
            "labels": [],
        }
        fields = mapper.extract_fields(item_data)
        assert fields["story_points"] == 5
        assert fields["business_value"] == 25
        assert fields["value_points"] == 5  # 25 / 5 = 5

    def test_map_from_canonical(self) -> None:
        """Test mapping canonical fields back to GitHub markdown format."""
        mapper = GitHubFieldMapper()
        canonical_fields = {
            "description": "Main description",
            "acceptance_criteria": "Criterion 1\nCriterion 2",
            "story_points": 8,
            "business_value": 50,
            "priority": 2,
        }
        github_fields = mapper.map_from_canonical(canonical_fields)
        assert "body" in github_fields
        body = github_fields["body"]
        assert "Main description" in body
        assert "## Acceptance Criteria" in body
        assert "Criterion 1" in body
        assert "## Story Points" in body
        assert "8" in body
        assert "## Business Value" in body
        assert "50" in body
        assert "## Priority" in body
        assert "2" in body


class TestAdoFieldMapper:
    """Tests for AdoFieldMapper with default mappings."""

    def test_extract_description_from_system_description(self) -> None:
        """Test extracting description from System.Description field."""
        mapper = AdoFieldMapper()
        item_data = {
            "fields": {
                "System.Description": "This is the description",
                "System.Title": "Test Item",
            }
        }
        fields = mapper.extract_fields(item_data)
        assert fields["description"] == "This is the description"

    def test_extract_acceptance_criteria_from_field(self) -> None:
        """Test extracting acceptance criteria from System.AcceptanceCriteria field."""
        mapper = AdoFieldMapper()
        item_data = {
            "fields": {
                "System.Description": "Description",
                "System.AcceptanceCriteria": "AC1\nAC2",
                "System.Title": "Test Item",
            }
        }
        fields = mapper.extract_fields(item_data)
        assert fields["acceptance_criteria"] == "AC1\nAC2"

    def test_extract_story_points_from_microsoft_vsts_common(self) -> None:
        """Test extracting story points from Microsoft.VSTS.Common.StoryPoints."""
        mapper = AdoFieldMapper()
        item_data = {
            "fields": {
                "System.Description": "Description",
                "Microsoft.VSTS.Common.StoryPoints": 8,
                "System.Title": "Test Item",
            }
        }
        fields = mapper.extract_fields(item_data)
        assert fields["story_points"] == 8

    def test_extract_story_points_from_microsoft_vsts_scheduling(self) -> None:
        """Test extracting story points from Microsoft.VSTS.Scheduling.StoryPoints."""
        mapper = AdoFieldMapper()
        item_data = {
            "fields": {
                "System.Description": "Description",
                "Microsoft.VSTS.Scheduling.StoryPoints": 13,
                "System.Title": "Test Item",
            }
        }
        fields = mapper.extract_fields(item_data)
        assert fields["story_points"] == 13

    def test_extract_business_value(self) -> None:
        """Test extracting business value from Microsoft.VSTS.Common.BusinessValue."""
        mapper = AdoFieldMapper()
        item_data = {
            "fields": {
                "System.Description": "Description",
                "Microsoft.VSTS.Common.BusinessValue": 75,
                "System.Title": "Test Item",
            }
        }
        fields = mapper.extract_fields(item_data)
        assert fields["business_value"] == 75

    def test_extract_priority(self) -> None:
        """Test extracting priority from Microsoft.VSTS.Common.Priority."""
        mapper = AdoFieldMapper()
        item_data = {
            "fields": {
                "System.Description": "Description",
                "Microsoft.VSTS.Common.Priority": 2,
                "System.Title": "Test Item",
            }
        }
        fields = mapper.extract_fields(item_data)
        assert fields["priority"] == 2

    def test_extract_work_item_type(self) -> None:
        """Test extracting work item type from System.WorkItemType."""
        mapper = AdoFieldMapper()
        item_data = {
            "fields": {
                "System.Description": "Description",
                "System.WorkItemType": "User Story",
                "System.Title": "Test Item",
            }
        }
        fields = mapper.extract_fields(item_data)
        assert fields["work_item_type"] == "User Story"

    def test_calculate_value_points(self) -> None:
        """Test calculating value points from business_value / story_points."""
        mapper = AdoFieldMapper()
        item_data = {
            "fields": {
                "System.Description": "Description",
                "Microsoft.VSTS.Common.StoryPoints": 5,
                "Microsoft.VSTS.Common.BusinessValue": 25,
                "System.Title": "Test Item",
            }
        }
        fields = mapper.extract_fields(item_data)
        assert fields["story_points"] == 5
        assert fields["business_value"] == 25
        assert fields["value_points"] == 5  # 25 / 5 = 5

    def test_clamp_story_points_to_range(self) -> None:
        """Test that story points are clamped to 0-100 range."""
        mapper = AdoFieldMapper()
        item_data = {
            "fields": {
                "System.Description": "Description",
                "Microsoft.VSTS.Common.StoryPoints": 150,  # Out of range
                "System.Title": "Test Item",
            }
        }
        fields = mapper.extract_fields(item_data)
        assert fields["story_points"] == 100  # Clamped to max

    def test_clamp_priority_to_range(self) -> None:
        """Test that priority is clamped to 1-4 range."""
        mapper = AdoFieldMapper()
        item_data = {
            "fields": {
                "System.Description": "Description",
                "Microsoft.VSTS.Common.Priority": 10,  # Out of range
                "System.Title": "Test Item",
            }
        }
        fields = mapper.extract_fields(item_data)
        assert fields["priority"] == 4  # Clamped to max

    def test_map_from_canonical(self) -> None:
        """Test mapping canonical fields back to ADO field format."""
        mapper = AdoFieldMapper()
        canonical_fields = {
            "description": "Main description",
            "acceptance_criteria": "Criterion 1",
            "story_points": 8,
            "business_value": 50,
            "priority": 2,
            "work_item_type": "User Story",
        }
        ado_fields = mapper.map_from_canonical(canonical_fields)
        assert "System.Description" in ado_fields
        assert ado_fields["System.Description"] == "Main description"
        assert "System.AcceptanceCriteria" in ado_fields
        assert ado_fields["System.AcceptanceCriteria"] == "Criterion 1"
        # ADO mapper may use either Microsoft.VSTS.Common.StoryPoints or Microsoft.VSTS.Scheduling.StoryPoints
        # Both are valid, check for either (reverse mapping picks first match)
        assert (
            "Microsoft.VSTS.Common.StoryPoints" in ado_fields or "Microsoft.VSTS.Scheduling.StoryPoints" in ado_fields
        )
        story_points_value = ado_fields.get("Microsoft.VSTS.Common.StoryPoints") or ado_fields.get(
            "Microsoft.VSTS.Scheduling.StoryPoints"
        )
        assert story_points_value == 8
        assert "Microsoft.VSTS.Common.BusinessValue" in ado_fields
        assert ado_fields["Microsoft.VSTS.Common.BusinessValue"] == 50
        assert "Microsoft.VSTS.Common.Priority" in ado_fields
        assert ado_fields["Microsoft.VSTS.Common.Priority"] == 2
        assert "System.WorkItemType" in ado_fields
        assert ado_fields["System.WorkItemType"] == "User Story"


class TestCustomTemplateMapping:
    """Tests for custom template mapping support."""

    def test_load_custom_mapping_from_file(self, tmp_path: Path) -> None:
        """Test loading custom field mapping from YAML file."""
        # Create custom mapping file
        custom_mapping_file = tmp_path / "ado_custom.yaml"
        custom_mapping_data = {
            "framework": "scrum",
            "field_mappings": {
                "Custom.StoryPoints": "story_points",
                "Custom.BusinessValue": "business_value",
            },
            "work_item_type_mappings": {
                "Product Backlog Item": "User Story",
            },
        }
        custom_mapping_file.write_text(yaml.dump(custom_mapping_data), encoding="utf-8")

        # Create mapper with custom mapping
        mapper = AdoFieldMapper(custom_mapping_file=custom_mapping_file)

        # Test that custom mappings are used
        item_data = {
            "fields": {
                "System.Description": "Description",
                "Custom.StoryPoints": 8,
                "Custom.BusinessValue": 50,
                "System.WorkItemType": "Product Backlog Item",
                "System.Title": "Test Item",
            }
        }
        fields = mapper.extract_fields(item_data)
        assert fields["story_points"] == 8
        assert fields["business_value"] == 50
        assert fields["work_item_type"] == "User Story"  # Mapped via work_item_type_mappings

    def test_custom_mapping_overrides_defaults(self, tmp_path: Path) -> None:
        """Test that custom mappings override default mappings."""
        # Create custom mapping file that overrides default
        custom_mapping_file = tmp_path / "ado_custom.yaml"
        custom_mapping_data = {
            "field_mappings": {
                "System.Description": "description",
                "Custom.AcceptanceCriteria": "acceptance_criteria",  # Override default
            },
        }
        custom_mapping_file.write_text(yaml.dump(custom_mapping_data), encoding="utf-8")

        mapper = AdoFieldMapper(custom_mapping_file=custom_mapping_file)

        item_data = {
            "fields": {
                "System.Description": "Description",
                "Custom.AcceptanceCriteria": "Custom AC",
                "System.Title": "Test Item",
            }
        }
        fields = mapper.extract_fields(item_data)
        # Should use custom mapping, not default System.AcceptanceCriteria
        assert fields["acceptance_criteria"] == "Custom AC"

    def test_fallback_to_defaults_when_custom_not_found(self) -> None:
        """Test that mapper falls back to defaults when custom mapping file not found."""
        mapper = AdoFieldMapper(custom_mapping_file=Path("/nonexistent/file.yaml"))

        # Should still work with defaults (warns but continues)
        item_data = {
            "fields": {
                "System.Description": "Description",
                "System.AcceptanceCriteria": "Default AC",
                "System.Title": "Test Item",
            }
        }
        fields = mapper.extract_fields(item_data)
        assert fields["description"] == "Description"
        assert fields["acceptance_criteria"] == "Default AC"

    def test_auto_detect_custom_mapping_from_specfact_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test auto-detection of custom mapping from .specfact/ directory."""
        # Create .specfact directory structure
        specfact_dir = tmp_path / ".specfact" / "templates" / "backlog" / "field_mappings"
        specfact_dir.mkdir(parents=True, exist_ok=True)
        custom_mapping_file = specfact_dir / "ado_custom.yaml"

        custom_mapping_data = {
            "field_mappings": {
                "Custom.Field": "description",
            },
        }
        custom_mapping_file.write_text(yaml.dump(custom_mapping_data), encoding="utf-8")

        # Change to tmp_path so auto-detection works
        monkeypatch.chdir(tmp_path)

        mapper = AdoFieldMapper()  # No custom_mapping_file parameter - should auto-detect

        item_data = {
            "fields": {
                "Custom.Field": "Custom Description",
                "System.Title": "Test Item",
            }
        }
        fields = mapper.extract_fields(item_data)
        assert fields["description"] == "Custom Description"
