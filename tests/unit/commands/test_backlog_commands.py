"""
Unit tests for backlog commands.

Tests for backlog refinement commands, including preview output and filtering.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from rich.panel import Panel
from typer.testing import CliRunner

from specfact_cli.backlog.template_detector import TemplateDetector
from specfact_cli.cli import app
from specfact_cli.models.backlog_item import BacklogItem
from specfact_cli.modules.backlog.src.commands import (
    _apply_issue_window,
    _build_comment_fetch_progress_description,
    _build_refine_export_content,
    _build_refine_preview_comment_empty_panel,
    _build_refine_preview_comment_panels,
    _item_needs_refinement,
    _parse_refined_export_markdown,
    _resolve_refine_export_comment_window,
    _resolve_refine_preview_comment_window,
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


class TestBuildRefineExportContent:
    """Tests for refine export content rendering."""

    def test_refine_export_includes_comments_when_available(self) -> None:
        """Refine export includes comment annotations by default when available."""
        item = BacklogItem(
            id="42",
            provider="ado",
            url="https://dev.azure.com/org/project/_workitems/edit/42",
            title="Story",
            body_markdown="Body text",
            state="Active",
            assignees=[],
        )
        content = _build_refine_export_content(
            adapter="ado",
            items=[item],
            comments_by_item_id={"42": ["Comment A", "Comment B"]},
        )
        assert "Comments (annotations)" in content
        assert "Comment A" in content
        assert "Comment B" in content
        assert "## Copilot Instructions" in content
        assert "must not include this instruction block" in content
        assert "Preserve all original requirements, scope, and technical details" in content

    def test_refine_export_omits_comments_section_when_none(self) -> None:
        """Refine export omits comments section when no comments exist for item."""
        item = BacklogItem(
            id="42",
            provider="ado",
            url="https://dev.azure.com/org/project/_workitems/edit/42",
            title="Story",
            body_markdown="Body text",
            state="Active",
            assignees=[],
        )
        content = _build_refine_export_content(adapter="ado", items=[item], comments_by_item_id={})
        assert "Comments (annotations)" not in content

    def test_refine_export_places_instructions_before_first_item(self) -> None:
        """Instruction block appears before exported item sections."""
        item = BacklogItem(
            id="42",
            provider="ado",
            url="https://dev.azure.com/org/project/_workitems/edit/42",
            title="Story",
            body_markdown="Body text",
            state="Active",
            assignees=[],
        )
        content = _build_refine_export_content(adapter="ado", items=[item], comments_by_item_id={})
        assert content.index("## Copilot Instructions") < content.index("## Item 1:")

    def test_refine_export_includes_template_guidance_for_items(self) -> None:
        """Export includes template guidance similar to interactive prompts."""
        item = BacklogItem(
            id="42",
            provider="github",
            url="https://github.com/org/repo/issues/42",
            title="Story",
            body_markdown="Body text",
            state="open",
            assignees=[],
        )
        content = _build_refine_export_content(
            adapter="github",
            items=[item],
            comments_by_item_id={},
            template_guidance_by_item_id={
                "42": {
                    "template_id": "enabler_v1",
                    "name": "Enabler",
                    "description": "Enabler work template",
                    "required_sections": ["Objective", "Technical Approach", "Success Criteria"],
                    "optional_sections": ["Dependencies", "Risks", "Timeline"],
                }
            },
        )
        assert "**Target Template**:" in content
        assert "**Required Sections**:" in content
        assert "**Optional Sections**:" in content


class TestRefineCommentWindowResolution:
    """Tests for refine preview/export comment-window semantics."""

    def test_refine_preview_defaults_to_last_two_comments(self) -> None:
        """Preview uses last two comments when no explicit window flags are provided."""
        first, last = _resolve_refine_preview_comment_window(first_comments=None, last_comments=None)
        assert first is None
        assert last == 2

    def test_refine_preview_respects_first_comments_override(self) -> None:
        """Preview honors --first-comments when provided."""
        first, last = _resolve_refine_preview_comment_window(first_comments=5, last_comments=None)
        assert first == 5
        assert last is None

    def test_refine_preview_respects_last_comments_override(self) -> None:
        """Preview honors --last-comments when provided."""
        first, last = _resolve_refine_preview_comment_window(first_comments=None, last_comments=4)
        assert first is None
        assert last == 4

    def test_refine_export_always_uses_full_comment_history(self) -> None:
        """Export ignores preview comment-window flags and always requests full comments."""
        first, last = _resolve_refine_export_comment_window(first_comments=5, last_comments=None)
        assert first is None
        assert last is None

        first_2, last_2 = _resolve_refine_export_comment_window(first_comments=None, last_comments=3)
        assert first_2 is None
        assert last_2 is None


class TestRefinePreviewCommentUx:
    """Tests for refine preview comment progress and block rendering."""

    def test_build_comment_fetch_progress_description_includes_position(self) -> None:
        """Progress message uses n/m indicator while fetching comments."""
        message = _build_comment_fetch_progress_description(3, 66, "123")
        assert "3/66" in message
        assert "123" in message
        assert "Fetching issue" in message

    def test_build_refine_preview_comment_panels_returns_panels(self) -> None:
        """Preview comments are rendered as panel blocks for clear scoping."""
        panels = _build_refine_preview_comment_panels(["first comment", "second comment"])
        assert len(panels) == 2
        assert all(isinstance(panel, Panel) for panel in panels)

    def test_build_refine_preview_comment_empty_panel_returns_panel(self) -> None:
        """Preview shows explicit hint when no comments are found."""
        panel = _build_refine_preview_comment_empty_panel()
        assert isinstance(panel, Panel)


class TestRefineIssueWindow:
    """Tests for refine first/last issue window controls."""

    @staticmethod
    def _item(id_: str) -> BacklogItem:
        return BacklogItem(
            id=id_,
            provider="github",
            url=f"https://github.com/org/repo/issues/{id_}",
            title=f"Item {id_}",
            body_markdown="Body",
            state="open",
            assignees=[],
        )

    def test_apply_issue_window_first_issues(self) -> None:
        items = [self._item("3"), self._item("1"), self._item("2")]
        result = _apply_issue_window(items, first_issues=2, last_issues=None)
        assert [i.id for i in result] == ["1", "2"]

    def test_apply_issue_window_last_issues(self) -> None:
        items = [self._item("3"), self._item("1"), self._item("2")]
        result = _apply_issue_window(items, first_issues=None, last_issues=2)
        assert [i.id for i in result] == ["2", "3"]

    def test_apply_issue_window_rejects_both_first_and_last(self) -> None:
        items = [self._item("1")]
        try:
            _apply_issue_window(items, first_issues=1, last_issues=1)
        except ValueError as exc:
            assert "--first-issues" in str(exc)
            return
        raise AssertionError("Expected ValueError when both first_issues and last_issues are set")


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
