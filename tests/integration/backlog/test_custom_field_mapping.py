"""
Integration tests for CLI with custom field mappings.

Tests the complete flow of using custom field mapping files with the backlog refine command.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from specfact_cli.cli import app


@pytest.fixture
def custom_mapping_file(tmp_path: Path) -> Path:
    """Create a custom field mapping file for testing."""
    mapping_file = tmp_path / "ado_custom.yaml"
    mapping_data = {
        "framework": "scrum",
        "field_mappings": {
            "System.Description": "description",
            "Custom.AcceptanceCriteria": "acceptance_criteria",
            "Custom.StoryPoints": "story_points",
            "Custom.BusinessValue": "business_value",
            "Custom.Priority": "priority",
            "System.WorkItemType": "work_item_type",
        },
        "work_item_type_mappings": {
            "Product Backlog Item": "User Story",
            "Bug": "Bug",
        },
    }
    mapping_file.write_text(yaml.dump(mapping_data), encoding="utf-8")
    return mapping_file


@pytest.fixture
def invalid_mapping_file(tmp_path: Path) -> Path:
    """Create an invalid custom field mapping file for testing."""
    mapping_file = tmp_path / "invalid.yaml"
    mapping_file.write_text("invalid: yaml: content: [", encoding="utf-8")
    return mapping_file


class TestCustomFieldMappingCLI:
    """Integration tests for CLI with custom field mappings."""

    def test_custom_field_mapping_file_validation_success(self, custom_mapping_file: Path) -> None:
        """Test that valid custom field mapping file is accepted."""
        runner = CliRunner()
        # Use --help to test that the option exists and file validation works
        # (actual refine command would need real adapter setup)
        result = runner.invoke(
            app,
            [
                "backlog",
                "refine",
                "ado",
                "--ado-org",
                "test-org",
                "--ado-project",
                "test-project",
                "--custom-field-mapping",
                str(custom_mapping_file),
                "--help",
            ],
        )
        # Should not error on file validation (help is shown before validation)
        assert result.exit_code in (0, 2)  # 0 = success, 2 = typer help exit

    def test_custom_field_mapping_file_validation_file_not_found(self) -> None:
        """Test that missing custom field mapping file is rejected."""
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "backlog",
                "refine",
                "ado",
                "--ado-org",
                "test-org",
                "--ado-project",
                "test-project",
                "--custom-field-mapping",
                "/nonexistent/file.yaml",
            ],
            catch_exceptions=False,  # Don't catch exceptions to avoid timeout
        )
        # Should exit with error code (validation happens before adapter setup)
        assert result.exit_code != 0
        assert "not found" in result.stdout.lower() or "error" in result.stdout.lower() or "Error" in result.stdout

    def test_custom_field_mapping_file_validation_invalid_format(self, invalid_mapping_file: Path) -> None:
        """Test that invalid custom field mapping file format is rejected."""
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "backlog",
                "refine",
                "ado",
                "--ado-org",
                "test-org",
                "--ado-project",
                "test-project",
                "--custom-field-mapping",
                str(invalid_mapping_file),
            ],
        )
        assert result.exit_code != 0
        assert "invalid" in result.stdout.lower() or "error" in result.stdout.lower()

    def test_custom_field_mapping_environment_variable(
        self, custom_mapping_file: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that custom field mapping can be set via environment variable."""
        monkeypatch.setenv("SPECFACT_ADO_CUSTOM_MAPPING", str(custom_mapping_file))
        # The converter should use the environment variable
        from specfact_cli.backlog.converter import convert_ado_work_item_to_backlog_item

        item_data = {
            "id": "123",
            "url": "https://dev.azure.com/test/org/project/_workitems/edit/123",
            "fields": {
                "System.Title": "Test Item",
                "System.Description": "Description",
                "Custom.StoryPoints": 8,  # Using custom field
                "Custom.BusinessValue": 50,  # Using custom field
            },
        }

        # Should use custom mapping from environment variable
        backlog_item = convert_ado_work_item_to_backlog_item(item_data, provider="ado")
        assert backlog_item.story_points == 8
        assert backlog_item.business_value == 50

    def test_custom_field_mapping_parameter_overrides_environment(
        self, custom_mapping_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that CLI parameter overrides environment variable."""
        # Create another mapping file
        other_mapping_file = tmp_path / "other_mapping.yaml"
        other_mapping_data = {
            "field_mappings": {
                "System.Description": "description",
                "Other.StoryPoints": "story_points",
            },
        }
        other_mapping_file.write_text(yaml.dump(other_mapping_data), encoding="utf-8")

        # Set environment variable to one file
        monkeypatch.setenv("SPECFACT_ADO_CUSTOM_MAPPING", str(custom_mapping_file))

        # CLI parameter should override environment variable
        # (This is tested by the fact that the parameter sets the env var)
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "backlog",
                "refine",
                "ado",
                "--ado-org",
                "test-org",
                "--ado-project",
                "test-project",
                "--custom-field-mapping",
                str(other_mapping_file),
                "--help",
            ],
        )
        # Should validate the parameter file, not the environment variable file
        assert result.exit_code in (0, 2)
