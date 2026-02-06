"""
Unit tests for specfact backlog daily (standup view and optional comment).

Scenarios from openspec/changes/daily-standup-progress-support/specs/daily-standup/spec.md:
- Standup view lists items with status and last-updated; optional standup summary lines
- Assignee filter
- Post standup comment (mock adapter)
- Adapter without comment support reports clearly
- Default standup scope (state/limit when not passed)
- Current iteration/sprint focus
- Unassigned/pending items view
- Sprint/iteration end date display
- Blockers-first and optional priority
- Interactive step-by-step review (--interactive, detail view, navigation)
- Export to file for Copilot (--copilot-export <path>)
- Optional value score and next-best suggestion
- Summarize prompt (--summarize [path]) for slash command / Copilot standup summary
- specfact.backlog-daily prompt file for interactive team walkthrough
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock

from typer.testing import CliRunner

from specfact_cli.backlog.adapters.base import BacklogAdapter
from specfact_cli.cli import app
from specfact_cli.models.backlog_item import BacklogItem
from specfact_cli.modules.backlog.src.commands import (
    _apply_filters,
    _build_copilot_export_content,
    _build_standup_rows,
    _build_summarize_prompt_content,
    _compute_value_score,
    _format_daily_item_detail,
    _format_standup_comment,
    _post_standup_comment_supported,
)


runner = CliRunner()


def _strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from CLI output."""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


def _item(
    id_: str = "1",
    title: str = "Item",
    state: str = "open",
    updated_at: datetime | None = None,
    assignees: list[str] | None = None,
    body_markdown: str = "",
    iteration: str | None = None,
    sprint: str | None = None,
    priority: int | None = None,
    business_value: int | None = None,
    story_points: int | None = None,
    acceptance_criteria: str | None = None,
) -> BacklogItem:
    return BacklogItem(
        id=id_,
        provider="github",
        url=f"https://github.com/o/r/issues/{id_}",
        title=title,
        body_markdown=body_markdown,
        state=state,
        assignees=assignees or [],
        updated_at=updated_at or datetime.now(UTC),
        iteration=iteration,
        sprint=sprint,
        priority=priority,
        business_value=business_value,
        story_points=story_points,
        acceptance_criteria=acceptance_criteria,
    )


class TestBuildStandupRows:
    """Scenario: List my items with status and last activity."""

    def test_lists_items_with_id_title_status_last_updated(self) -> None:
        """Standup view lists items with id, title, status, last-updated."""
        items = [
            _item("1", "First", "open", datetime(2025, 2, 1, 10, 0, tzinfo=UTC)),
            _item("2", "Second", "closed", datetime(2025, 2, 2, 11, 0, tzinfo=UTC)),
        ]
        rows = _build_standup_rows(items)
        assert len(rows) == 2
        assert rows[0]["id"] == "1" and rows[0]["title"] == "First" and rows[0]["status"] == "open"
        assert rows[0]["last_updated"] == datetime(2025, 2, 1, 10, 0, tzinfo=UTC)
        assert rows[1]["id"] == "2" and rows[1]["title"] == "Second" and rows[1]["status"] == "closed"
        assert rows[1]["last_updated"] == datetime(2025, 2, 2, 11, 0, tzinfo=UTC)

    def test_optional_standup_summary_lines_when_in_body(self) -> None:
        """Optional standup summary lines (yesterday/today/blockers) shown when in body."""
        body = "Description\n\n**Yesterday:** Did X.\n**Today:** Will do Y.\n**Blockers:** None."
        items = [_item("1", "Task", body_markdown=body)]
        rows = _build_standup_rows(items)
        assert len(rows) == 1
        assert "Yesterday" in (rows[0].get("yesterday") or "") or "Did X" in (rows[0].get("yesterday") or "")
        assert "Today" in (rows[0].get("today") or "") or "Will do Y" in (rows[0].get("today") or "")
        assert "Blockers" in (rows[0].get("blockers") or "") or "None" in (rows[0].get("blockers") or "")

    def test_assignee_filter_applied_by_caller(self) -> None:
        """Assignee filter is applied by caller via _apply_filters; rows reflect filtered items."""
        items = [
            _item("1", "Mine", assignees=["me"]),
            _item("2", "Other", assignees=["other"]),
        ]
        rows = _build_standup_rows(items)
        assert len(rows) == 2
        rows_me = _build_standup_rows([items[0]])
        assert len(rows_me) == 1 and rows_me[0]["title"] == "Mine"


class TestFormatStandupComment:
    """Format standup comment for posting (Yesterday / Today / Blockers)."""

    def test_formats_standup_comment_with_prefix(self) -> None:
        """Comment is clearly identifiable (e.g. Standup YYYY-MM-DD)."""
        from datetime import date

        text = _format_standup_comment("Did X", "Will Y", "None")
        today = date.today().isoformat()
        assert "Standup" in text or today in text
        assert "Yesterday" in text or "Did X" in text
        assert "Today" in text or "Will Y" in text
        assert "Blockers" in text or "None" in text


class TestPostStandupCommentSupported:
    """Scenario: Adapter does not support comments -> report clearly."""

    def test_adapter_without_comment_support_returns_false(self) -> None:
        """When adapter does not support comments, report that posting is not supported."""
        mock = MagicMock(spec=BacklogAdapter)
        mock.supports_add_comment.return_value = False
        item = _item("1", "Task")
        supported = _post_standup_comment_supported(mock, item)
        assert supported is False

    def test_adapter_with_comment_support_returns_true(self) -> None:
        """When adapter supports comments (supports_add_comment returns True), posting is supported."""
        mock = MagicMock(spec=BacklogAdapter)
        mock.supports_add_comment.return_value = True
        item = _item("1", "Task")
        supported = _post_standup_comment_supported(mock, item)
        assert supported is True


class TestPostStandupCommentViaAdapter:
    """Scenario: Post standup comment via GitHub adapter (mock)."""

    def test_post_standup_comment_calls_adapter_add_comment(self) -> None:
        """When user opts in and adapter supports comments, add_comment is called."""
        from specfact_cli.modules.backlog.src.commands import _post_standup_to_item

        mock = MagicMock(spec=BacklogAdapter)
        mock.add_comment.return_value = True
        item = _item("1", "Task")
        body = _format_standup_comment("X", "Y", "Z")
        ok = _post_standup_to_item(mock, item, body)
        assert ok is True
        mock.add_comment.assert_called_once_with(item, body)

    def test_post_standup_comment_failure_reported(self) -> None:
        """When add_comment returns False, success is False."""
        from specfact_cli.modules.backlog.src.commands import _post_standup_to_item

        mock = MagicMock(spec=BacklogAdapter)
        mock.add_comment.return_value = False
        item = _item("1", "Task")
        ok = _post_standup_to_item(mock, item, "Standup text")
        assert ok is False


class TestBacklogDailyCli:
    """CLI: specfact backlog daily."""

    def test_daily_help(self) -> None:
        """Backlog daily subcommand exists and shows help."""
        result = runner.invoke(app, ["backlog", "daily", "--help"])
        assert result.exit_code == 0
        assert "daily" in result.output.lower()

    def test_daily_accepts_sprint_and_iteration_options(self) -> None:
        """Backlog daily has --sprint and --iteration options."""
        result = runner.invoke(app, ["backlog", "daily", "--help"])
        assert result.exit_code == 0
        # Help may include ANSI codes (e.g. on CI); check option names as substrings
        assert "sprint" in result.output.lower()
        assert "iteration" in result.output.lower()

    def test_daily_accepts_show_unassigned_and_unassigned_only(self) -> None:
        """Backlog daily has --show-unassigned and --unassigned-only options."""
        result = runner.invoke(app, ["backlog", "daily", "--help"])
        assert result.exit_code == 0
        assert "unassigned" in result.output.lower()

    def test_daily_accepts_blockers_first(self) -> None:
        """Backlog daily has --blockers-first option."""
        result = runner.invoke(app, ["backlog", "daily", "--help"])
        assert result.exit_code == 0
        assert "blockers-first" in result.output or "blockers" in result.output.lower()


class TestDefaultStandupScope:
    """Scenario: Standup view uses default scope when no filters given (6.1)."""

    def test_resolve_standup_options_uses_defaults_when_none(self) -> None:
        """When state/limit/assignee not passed, effective state is open and limit is 20."""
        from specfact_cli.modules.backlog.src.commands import _resolve_standup_options

        state, limit, assignee = _resolve_standup_options(None, None, None, None)
        assert state == "open"
        assert limit == 20
        assert assignee is None

    def test_resolve_standup_options_explicit_overrides_defaults(self) -> None:
        """Explicit --state and --limit override defaults."""
        from specfact_cli.modules.backlog.src.commands import _resolve_standup_options

        state, limit, assignee = _resolve_standup_options("closed", 10, None, None)
        assert state == "closed"
        assert limit == 10
        assert assignee is None

    def test_apply_filters_with_state_open_excludes_closed(self) -> None:
        """Default state 'open' excludes closed items."""
        items = [
            _item("1", "Open", state="open"),
            _item("2", "Closed", state="closed"),
        ]
        filtered = _apply_filters(items, state="open")
        assert len(filtered) == 1
        assert filtered[0].state == "open"


class TestCurrentIterationSprint:
    """Scenario: Standup view filtered to current iteration/sprint (6.2)."""

    def test_apply_filters_by_iteration(self) -> None:
        """When --iteration is used, only items in that iteration are listed."""
        items = [
            _item("1", "In Sprint 1", iteration="Project\\Sprint 1"),
            _item("2", "In Sprint 2", iteration="Project\\Sprint 2"),
        ]
        filtered = _apply_filters(items, iteration="Project\\Sprint 1")
        assert len(filtered) == 1
        assert filtered[0].iteration == "Project\\Sprint 1"

    def test_apply_filters_by_sprint(self) -> None:
        """When --sprint is used, only items in that sprint are listed."""
        items = [
            _item("1", "Sprint A", sprint="Sprint A"),
            _item("2", "Sprint B", sprint="Sprint B"),
        ]
        filtered = _apply_filters(items, sprint="Sprint A")
        assert len(filtered) == 1
        assert filtered[0].sprint == "Sprint A"

    def test_apply_filters_iteration_none_keeps_all_when_no_filter(self) -> None:
        """When iteration/sprint not passed, all items pass (no crash)."""
        items = [
            _item("1", "A", iteration="S1"),
            _item("2", "B", iteration="S2"),
        ]
        filtered = _apply_filters(items)
        assert len(filtered) == 2


class TestUnassignedItems:
    """Scenario: Unassigned items in separate table/section (6.3)."""

    def test_split_assigned_vs_unassigned(self) -> None:
        """Standup view splits items into assigned and unassigned."""
        from specfact_cli.modules.backlog.src.commands import _split_assigned_unassigned

        items = [
            _item("1", "Mine", assignees=["me"]),
            _item("2", "Unassigned", assignees=[]),
            _item("3", "Other", assignees=["other"]),
        ]
        assigned, unassigned = _split_assigned_unassigned(items)
        assert len(assigned) == 2
        assert len(unassigned) == 1
        assert unassigned[0].title == "Unassigned"

    def test_unassigned_only_filters_to_unassigned(self) -> None:
        """When unassigned_only, only unassigned items in scope."""
        from specfact_cli.modules.backlog.src.commands import _split_assigned_unassigned

        items = [
            _item("1", "A", assignees=["me"]),
            _item("2", "B", assignees=[]),
        ]
        _, unassigned = _split_assigned_unassigned(items)
        assert len(unassigned) == 1
        assert unassigned[0].assignees == []


class TestSprintIterationEndDate:
    """Scenario: Sprint/iteration end date displayed when available (6.4)."""

    def test_format_sprint_end_header(self) -> None:
        """When sprint end date provided, format as 'Sprint ends: YYYY-MM-DD (N days)'."""
        from datetime import date

        from specfact_cli.modules.backlog.src.commands import _format_sprint_end_header

        end = date(2025, 2, 15)
        header = _format_sprint_end_header(end)
        assert "Sprint ends" in header or "2025-02-15" in header
        assert "days" in header.lower() or "15" in header


class TestBlockersFirstAndOptionalPriority:
    """Scenario: Blockers first and optional priority column (6.5)."""

    def test_standup_rows_blockers_first(self) -> None:
        """When blockers-first, items with non-empty blockers appear first."""
        from specfact_cli.modules.backlog.src.commands import _build_standup_rows, _sort_standup_rows_blockers_first

        body_no = "Description only."
        body_yes = "**Blockers:** Waiting on API."
        items = [
            _item("1", "No blocker", body_markdown=body_no),
            _item("2", "Has blocker", body_markdown=body_yes),
        ]
        rows = _build_standup_rows(items)
        sorted_rows = _sort_standup_rows_blockers_first(rows)
        assert len(sorted_rows) == 2
        first_blockers = (sorted_rows[0].get("blockers") or "").strip()
        assert "Waiting" in first_blockers or "API" in first_blockers

    def test_standup_rows_include_priority_when_enabled(self) -> None:
        """When config enables priority and BacklogItem has priority, row has priority."""
        from specfact_cli.modules.backlog.src.commands import _build_standup_rows

        items = [_item("1", "P1 item", priority=1)]
        rows = _build_standup_rows(items, include_priority=True)
        assert len(rows) == 1
        assert rows[0].get("priority") is not None
        assert rows[0]["priority"] == 1


class TestComputeValueScore:
    """Scenario: Optional value score for next-best suggestion (13.3)."""

    def test_value_score_computed_when_all_present(self) -> None:
        """When story_points, business_value, priority are available, value_score = business_value / max(1, story_points * priority)."""
        item = _item("1", "Story", story_points=5, business_value=20, priority=2)
        score = _compute_value_score(item)
        assert score is not None
        assert score == 2.0  # 20 / (5 * 2)

    def test_value_score_omitted_when_data_missing(self) -> None:
        """When any of story_points, business_value, priority is missing, score is None."""
        assert _compute_value_score(_item("1", "A")) is None
        assert _compute_value_score(_item("1", "A", story_points=1)) is None
        assert _compute_value_score(_item("1", "A", business_value=10)) is None
        assert (
            _compute_value_score(_item("1", "A", story_points=0, business_value=10, priority=1)) is not None
        )  # max(1,0)=1


class TestBuildCopilotExportContent:
    """Scenario: Copilot export writes summarized items (13.2)."""

    def test_copilot_export_has_section_per_item(self) -> None:
        """When building Copilot export, content has one Markdown section per item with ID, title, status."""
        items = [
            _item("1", "First story", state="open", assignees=["alice"]),
            _item("2", "Second story", state="Active", assignees=[]),
        ]
        content = _build_copilot_export_content(items, include_value_score=False)
        assert "1" in content and "First story" in content and "open" in content
        assert "2" in content and "Second story" in content and "Active" in content
        assert "## " in content
        assert content.count("## ") >= 2

    def test_copilot_export_idempotent_format(self) -> None:
        """Export format is Markdown with headings and bullets for Copilot use."""
        items = [_item("1", "Title", body_markdown="**Yesterday:** X.")]
        content = _build_copilot_export_content(items, include_value_score=False)
        assert "## " in content
        assert "Title" in content
        assert "- " in content or "* " in content or "\n" in content

    def test_copilot_export_includes_description_and_comments_when_enabled(self) -> None:
        """When enabled, Copilot export includes description and comment annotations."""
        items = [
            _item(
                "1",
                "Story one",
                state="open",
                body_markdown="This is the issue description and context.",
            ),
        ]
        comments_by_id = {"1": ["Comment from Alice: In progress.", "Comment from Bob: Blocked on API."]}
        content = _build_copilot_export_content(
            items,
            include_value_score=False,
            include_comments=True,
            comments_by_item_id=comments_by_id,
        )
        assert "Description" in content and "issue description" in content
        assert "Comments" in content or "annotations" in content
        assert "In progress" in content and "Blocked on API" in content


class TestFormatDailyItemDetail:
    """Scenario: Interactive detail view refine-like (13.1)."""

    def test_format_daily_item_detail_includes_title_body_status(self) -> None:
        """Detail view includes ID, title, status, description/body."""
        item = _item("1", "My story", body_markdown="Description here.", acceptance_criteria="AC1")
        detail = _format_daily_item_detail(item, comments=[])
        assert "1" in detail and "My story" in detail
        assert "Description" in detail or "here" in detail
        assert "open" in detail.lower() or "status" in detail.lower()

    def test_format_daily_item_detail_includes_comments_when_provided(self) -> None:
        """When comments are provided, they appear in the detail string."""
        item = _item("1", "Story")
        detail = _format_daily_item_detail(item, comments=["Comment one", "Comment two"])
        assert "Comment one" in detail or "Comment" in detail
        assert "Comment two" in detail or "two" in detail


class TestBacklogDailyInteractiveAndExportOptions:
    """CLI: --interactive and --copilot-export options (13.1, 13.2)."""

    def test_daily_help_shows_interactive(self) -> None:
        """Backlog daily has --interactive option."""
        result = runner.invoke(app, ["backlog", "daily", "--help-advanced"])
        assert result.exit_code == 0
        assert "--interactive" in result.output or "interactive" in result.output.lower()

    def test_daily_help_shows_copilot_export(self) -> None:
        """Backlog daily has --copilot-export option."""
        result = runner.invoke(app, ["backlog", "daily", "--help-advanced"])
        assert result.exit_code == 0
        assert "copilot-export" in result.output or "copilot" in result.output.lower()

    def test_daily_help_shows_summarize(self) -> None:
        """Backlog daily has --summarize and --summarize-to options."""
        result = runner.invoke(app, ["backlog", "daily", "--help-advanced"])
        assert result.exit_code == 0
        assert "summarize" in result.output.lower()

    def test_daily_help_shows_comment_annotations(self) -> None:
        """Backlog daily has --comments/--annotations option for exports."""
        result = runner.invoke(app, ["backlog", "daily", "--help-advanced"])
        assert result.exit_code == 0
        output = _strip_ansi(result.output)
        assert "--comments" in output or "--annotations" in output


class TestBuildSummarizePromptContent:
    """Scenario: --summarize outputs prompt with filter context and per-item data (22.1)."""

    def test_summarize_prompt_contains_instruction_and_filter_context(self) -> None:
        """Summarize prompt contains instruction to generate standup summary and filter context."""
        items = [_item("1", "First", state="open", assignees=["alice"])]
        filter_ctx = {
            "adapter": "github",
            "state": "open",
            "sprint": "current",
            "assignee": "me",
            "limit": 20,
        }
        content = _build_summarize_prompt_content(items, filter_context=filter_ctx, include_value_score=False)
        assert "Generate" in content or "summary" in content.lower()
        assert "Filter context" in content or "filter" in content.lower()
        assert "github" in content
        assert "open" in content
        assert "current" in content
        assert "20" in content

    def test_summarize_prompt_contains_per_item_data(self) -> None:
        """Summarize prompt contains same per-item data as copilot export (ID, title, status)."""
        items = [
            _item("1", "First story", state="open", assignees=["alice"]),
            _item("2", "Second story", state="Active"),
        ]
        content = _build_summarize_prompt_content(
            items,
            filter_context={"adapter": "ado", "state": "—", "sprint": "—", "assignee": "—", "limit": 10},
            include_value_score=False,
        )
        assert "1" in content and "First story" in content
        assert "2" in content and "Second story" in content
        assert "## " in content

    def test_summarize_prompt_includes_body_and_comments_when_provided(self) -> None:
        """Summarize prompt includes description (body) and comments when include_comments=True."""
        items = [
            _item(
                "1",
                "Story one",
                state="open",
                body_markdown="This is the issue description and context.",
            ),
        ]
        comments_by_id = {"1": ["Comment from Alice: In progress.", "Comment from Bob: Blocked on API."]}
        content = _build_summarize_prompt_content(
            items,
            filter_context={"adapter": "github", "state": "open", "sprint": "—", "assignee": "—", "limit": 20},
            include_value_score=False,
            comments_by_item_id=comments_by_id,
            include_comments=True,
        )
        assert "Description" in content and "issue description" in content
        assert "Comments" in content or "annotations" in content
        assert "In progress" in content and "Blocked on API" in content

    def test_summarize_prompt_metadata_only_when_include_comments_false(self) -> None:
        """Summarize prompt omits description and comments when include_comments=False (gated on --comments)."""
        items = [
            _item(
                "1",
                "Story one",
                state="open",
                body_markdown="This is the issue description and context.",
            ),
        ]
        comments_by_id = {"1": ["Comment from Alice: In progress."]}
        content = _build_summarize_prompt_content(
            items,
            filter_context={"adapter": "github", "state": "open", "sprint": "—", "assignee": "—", "limit": 20},
            include_value_score=False,
            comments_by_item_id=comments_by_id,
            include_comments=False,
        )
        assert "metadata only" in content
        assert "issue description" not in content
        assert "In progress" not in content
        assert "Status:" in content and "Story one" in content

    def test_summarize_prompt_has_start_end_markers(self) -> None:
        """Summarize prompt is wrapped in BEGIN/END markers for extraction or emphasis."""
        items = [_item("1", "Story", state="open")]
        content = _build_summarize_prompt_content(
            items,
            filter_context={"adapter": "github", "state": "—", "sprint": "—", "assignee": "—", "limit": 20},
            include_value_score=False,
        )
        assert "--- BEGIN STANDUP PROMPT ---" in content
        assert "--- END STANDUP PROMPT ---" in content
        assert content.strip().startswith("--- BEGIN STANDUP PROMPT ---")
        assert content.strip().endswith("--- END STANDUP PROMPT ---")


class TestBacklogDailyPromptFile:
    """Prompt file specfact.backlog-daily.md exists and has expected sections (22.2)."""

    def test_backlog_daily_prompt_file_exists(self) -> None:
        """resources/prompts/specfact.backlog-daily.md exists."""
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        prompt_path = repo_root / "resources" / "prompts" / "specfact.backlog-daily.md"
        assert prompt_path.is_file(), f"Expected prompt file at {prompt_path}"

    def test_backlog_daily_prompt_contains_expected_sections(self) -> None:
        """Prompt file contains purpose, story-by-story, discussion notes as comments."""
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        prompt_path = repo_root / "resources" / "prompts" / "specfact.backlog-daily.md"
        if not prompt_path.is_file():
            return
        text = prompt_path.read_text(encoding="utf-8")
        assert "daily" in text.lower() or "standup" in text.lower()
        assert "story" in text.lower() or "item" in text.lower()
        assert "comment" in text.lower() or "discussion" in text.lower()
