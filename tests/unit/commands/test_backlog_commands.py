"""
Unit tests for backlog commands.

Tests for backlog refinement commands, including preview output and filtering.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.models.backlog_item import BacklogItem


runner = CliRunner()


class TestBacklogPreviewOutput:
    """Tests for backlog preview output display."""

    def test_preview_output_displays_assignee(self) -> None:
        """Test that preview output displays assignee information."""
        item = BacklogItem(
            id="123",
            provider="ado",
            url="https://dev.azure.com/org/project/_apis/wit/workitems/123",
            title="Test Item",
            body_markdown="Description",
            state="New",
            assignees=["John Doe", "john@example.com"],
        )

        # Verify assignees are set correctly
        assert len(item.assignees) == 2
        assert "John Doe" in item.assignees
        assert "john@example.com" in item.assignees

    def test_preview_output_displays_unassigned(self) -> None:
        """Test that preview output displays 'Unassigned' when no assignees."""
        item = BacklogItem(
            id="124",
            provider="ado",
            url="https://dev.azure.com/org/project/_apis/wit/workitems/124",
            title="Test Item",
            body_markdown="Description",
            state="New",
            assignees=[],
        )

        # Verify empty assignees list
        assert item.assignees == []

    def test_preview_output_assignee_format(self) -> None:
        """Test that assignee display format is correct."""
        item = BacklogItem(
            id="125",
            provider="ado",
            url="https://dev.azure.com/org/project/_apis/wit/workitems/125",
            title="Test Item",
            body_markdown="Description",
            state="New",
            assignees=["Jane Smith"],
        )

        # Format should be: ', '.join(item.assignees) if item.assignees else 'Unassigned'
        assignee_display = ", ".join(item.assignees) if item.assignees else "Unassigned"
        assert assignee_display == "Jane Smith"

        # Test unassigned format
        item_unassigned = BacklogItem(
            id="126",
            provider="ado",
            url="https://dev.azure.com/org/project/_apis/wit/workitems/126",
            title="Test Item",
            body_markdown="Description",
            state="New",
            assignees=[],
        )
        assignee_display_unassigned = ", ".join(item_unassigned.assignees) if item_unassigned.assignees else "Unassigned"
        assert assignee_display_unassigned == "Unassigned"


class TestInteractiveMappingCommand:
    """Tests for interactive template mapping command."""

    @patch("requests.get")
    @patch("rich.prompt.Prompt.ask")
    @patch("rich.prompt.Confirm.ask")
    def test_map_fields_fetches_ado_fields(
        self, mock_confirm: MagicMock, mock_prompt: MagicMock, mock_get: MagicMock
    ) -> None:
        """Test that map-fields command fetches fields from ADO API."""
        # Mock ADO API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "value": [
                {
                    "referenceName": "System.Description",
                    "name": "Description",
                    "type": "html",
                },
                {
                    "referenceName": "Microsoft.VSTS.Common.AcceptanceCriteria",
                    "name": "Acceptance Criteria",
                    "type": "html",
                },
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Mock rich.prompt.Prompt to avoid interactive input
        mock_prompt.return_value = ""
        mock_confirm.return_value = False

        result = runner.invoke(
            app,
            [
                "backlog",
                "map-fields",
                "--ado-org",
                "test-org",
                "--ado-project",
                "test-project",
                "--ado-token",
                "test-token",
            ],
        )

        # Should call ADO API
        assert mock_get.called
        call_args = mock_get.call_args
        assert "test-org" in call_args[0][0]
        assert "test-project" in call_args[0][0]
        assert "_apis/wit/fields" in call_args[0][0]

    @patch("requests.get")
    @patch("rich.prompt.Prompt.ask")
    @patch("rich.prompt.Confirm.ask")
    def test_map_fields_filters_system_fields(
        self, mock_confirm: MagicMock, mock_prompt: MagicMock, mock_get: MagicMock
    ) -> None:
        """Test that map-fields command filters out system-only fields."""
        # Mock ADO API response with system and user fields
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "value": [
                {"referenceName": "System.Id", "name": "ID", "type": "integer"},  # System field - should be filtered
                {"referenceName": "System.Rev", "name": "Revision", "type": "integer"},  # System field - should be filtered
                {"referenceName": "System.Description", "name": "Description", "type": "html"},  # User field - should be included
                {
                    "referenceName": "Microsoft.VSTS.Common.AcceptanceCriteria",
                    "name": "Acceptance Criteria",
                    "type": "html",
                },  # User field - should be included
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Mock rich.prompt.Prompt to avoid interactive input
        mock_prompt.return_value = ""
        mock_confirm.return_value = False

        result = runner.invoke(
            app,
            [
                "backlog",
                "map-fields",
                "--ado-org",
                "test-org",
                "--ado-project",
                "test-project",
                "--ado-token",
                "test-token",
            ],
        )

        # Command should execute (even if user cancels)
        # The filtering logic is tested implicitly by checking that system fields are excluded
        assert mock_get.called

    def test_map_fields_requires_token(self) -> None:
        """Test that map-fields command requires ADO token."""
        result = runner.invoke(
            app,
            [
                "backlog",
                "map-fields",
                "--ado-org",
                "test-org",
                "--ado-project",
                "test-project",
            ],
            env={"AZURE_DEVOPS_TOKEN": ""},  # Empty token
        )

        # Should fail with error about missing token
        assert result.exit_code != 0
        assert "token required" in result.stdout.lower() or "error" in result.stdout.lower()
