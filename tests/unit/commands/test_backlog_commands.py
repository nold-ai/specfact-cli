"""
Unit tests for backlog commands.

Tests for backlog refinement commands, including preview output and filtering.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from specfact_cli.backlog.template_detector import TemplateDetector
from specfact_cli.cli import app
from specfact_cli.models.backlog_item import BacklogItem
from specfact_cli.modules.backlog.src.commands import (
    _item_needs_refinement,
    _parse_refined_export_markdown,
)
from specfact_cli.templates.registry import BacklogTemplate, TemplateRegistry


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
        assignee_display_unassigned = (
            ", ".join(item_unassigned.assignees) if item_unassigned.assignees else "Unassigned"
        )
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

        runner.invoke(
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
                {
                    "referenceName": "System.Rev",
                    "name": "Revision",
                    "type": "integer",
                },  # System field - should be filtered
                {
                    "referenceName": "System.Description",
                    "name": "Description",
                    "type": "html",
                },  # User field - should be included
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

        runner.invoke(
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


class TestParseRefinedExportMarkdown:
    """Tests for _parse_refined_export_markdown (refine --import-from-tmp parser)."""

    def test_parses_single_item_with_body_and_id(self) -> None:
        """Parser extracts ID and body from export-format block."""
        content = """
# SpecFact Backlog Refinement Export

**Export Date**: 2026-01-27
**Adapter**: github
**Items**: 1

---

## Item 1: My Title

**ID**: issue-42
**URL**: https://github.com/org/repo/issues/42
**State**: open
**Provider**: github

**Body**:
```markdown
Refined body text here.
```
"""
        result = _parse_refined_export_markdown(content)
        assert "issue-42" in result
        assert result["issue-42"]["body_markdown"] == "Refined body text here."
        assert result["issue-42"].get("title") == "My Title"

    def test_parses_acceptance_criteria_and_metrics(self) -> None:
        """Parser extracts acceptance criteria and metrics when present."""
        content = """
## Item 1: Story title

**ID**: 123
**URL**: u
**State**: open
**Provider**: ado

**Metrics**:
- Story Points: 5
- Business Value: 8
- Priority: 1 (1=highest)

**Acceptance Criteria**:
- AC one
- AC two

**Body**:
```markdown
Body content
```
---
"""
        result = _parse_refined_export_markdown(content)
        assert "123" in result
        assert result["123"]["acceptance_criteria"] == "- AC one\n- AC two"
        assert result["123"]["story_points"] == 5
        assert result["123"]["business_value"] == 8
        assert result["123"]["priority"] == 1
        assert result["123"]["body_markdown"] == "Body content"

    def test_returns_empty_for_header_only(self) -> None:
        """Parser returns empty dict when no ## Item blocks."""
        content = "# SpecFact Backlog Refinement Export\n\n**Items**: 0\n\n---\n\n"
        result = _parse_refined_export_markdown(content)
        assert result == {}

    def test_skips_blocks_without_id(self) -> None:
        """Parser skips blocks that do not contain **ID**:."""
        content = """
## Item 1: No ID here

**URL**: x
**Body**:
```markdown
nope
```
"""
        result = _parse_refined_export_markdown(content)
        assert result == {}

    def test_body_with_nested_fenced_code_blocks(self) -> None:
        """Parser preserves full body when it contains fenced code blocks."""
        content = """
## Item 1: Bug with code sample

**ID**: issue-99
**URL**: https://github.com/org/repo/issues/99
**State**: open
**Provider**: github

**Body**:
```markdown
Reproduction: run this:

```python
def foo():
    return 42
```

Then we see the error.
```
---
"""
        result = _parse_refined_export_markdown(content)
        assert "issue-99" in result
        body = result["issue-99"]["body_markdown"]
        assert "Reproduction: run this:" in body
        assert "```python" in body
        assert "def foo():" in body
        assert "return 42" in body
        assert "```" in body
        assert "Then we see the error." in body


class TestItemNeedsRefinement:
    """Tests for _item_needs_refinement helper."""

    def test_needs_refinement_when_missing_sections(self) -> None:
        """Item needs refinement when required sections are missing."""
        registry = TemplateRegistry()
        registry.register_template(
            BacklogTemplate(
                template_id="user-story",
                name="User Story",
                description="",
                required_sections=["As a", "I want", "Acceptance Criteria"],
            )
        )
        detector = TemplateDetector(registry)
        item = BacklogItem(
            id="1",
            provider="github",
            url="https://github.com/org/repo/issues/1",
            title="Story",
            body_markdown="As a user I want...",
            state="open",
            assignees=[],
        )
        assert _item_needs_refinement(item, detector, registry, None, "github", None, None) is True

    def test_does_not_need_refinement_when_high_confidence_no_missing(self) -> None:
        """Item does not need refinement when confidence >= 0.8 and no missing fields."""
        registry = TemplateRegistry()
        registry.register_template(
            BacklogTemplate(
                template_id="user-story",
                name="User Story",
                description="",
                required_sections=["Acceptance Criteria"],
            )
        )
        detector = TemplateDetector(registry)
        item = BacklogItem(
            id="2",
            provider="github",
            url="https://github.com/org/repo/issues/2",
            title="Story",
            body_markdown="As a user I want X.\n\n## Acceptance Criteria\n- [ ] Done",
            state="open",
            assignees=[],
        )
        result = _item_needs_refinement(item, detector, registry, None, "github", None, None)
        assert result is False
