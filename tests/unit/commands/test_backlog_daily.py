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
from unittest.mock import MagicMock

import click
import pytest
import typer.main
from typer.testing import CliRunner


pytest.importorskip("specfact_backlog.backlog.commands")
from specfact_backlog.backlog.commands import (
    _apply_comment_window,
    _apply_filters,
    _apply_issue_id_filter,
    _build_copilot_export_content,
    _build_daily_interactive_comment_panels,
    _build_daily_navigation_choices,
    _build_daily_patch_proposal,
    _build_interactive_post_body,
    _build_standup_rows,
    _build_summarize_prompt_content,
    _compute_value_score,
    _format_daily_item_detail,
    _format_standup_comment,
    _post_standup_comment_supported,
    _resolve_daily_display_limit,
    _resolve_daily_fetch_limit,
    _resolve_daily_issue_window,
    _resolve_daily_mode_state,
    _resolve_post_fetch_assignee_filter,
    _split_exception_rows,
)

from specfact_cli.backlog.adapters.base import BacklogAdapter
from specfact_cli.cli import app
from specfact_cli.models.backlog_item import BacklogItem


runner = CliRunner()


@pytest.fixture(autouse=True)
def _bootstrap_registry_for_backlog_daily():
    """Ensure registry is bootstrapped so root 'backlog' resolves to the group with 'daily'."""
    from specfact_cli.registry.bootstrap import register_builtin_commands
    from specfact_cli.registry.registry import CommandRegistry

    CommandRegistry._clear_for_testing()
    register_builtin_commands()
    yield
    CommandRegistry._clear_for_testing()


def _strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from CLI output."""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


def _get_daily_command_option_names() -> set[str]:
    """Return all option names registered on `specfact backlog daily` (from CLI help or command tree)."""
    root_cmd = typer.main.get_command(app)
    root_ctx = click.Context(root_cmd)
    backlog_cmd = root_cmd.get_command(root_ctx, "backlog")
    assert backlog_cmd is not None, "root should have 'backlog' command"
    backlog_ctx = click.Context(backlog_cmd)
    daily_cmd = backlog_cmd.get_command(backlog_ctx, "daily")
    if daily_cmd is not None:
        option_names: set[str] = set()
        for param in daily_cmd.params:
            if isinstance(param, click.Option):
                option_names.update(param.opts)
                option_names.update(param.secondary_opts)
        return option_names
    result = runner.invoke(app, ["backlog", "daily", "--help"])
    if result.exit_code != 0:
        return set()
    out = result.output or result.stdout or ""
    option_names = set()
    for word in out.replace(",", " ").split():
        w = word.strip()
        if w.startswith("--") and "=" not in w:
            opt = w.lstrip("-").split("=")[0]
            option_names.add("--" + opt)
    if not option_names:
        import re

        for m in re.finditer(r"--([a-z][a-z0-9-]*)", out):
            option_names.add("--" + m.group(1))
    return option_names


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

    def test_row_includes_assignees_for_table_rendering(self) -> None:
        """Standup row carries assignees so table can show assignment context."""
        rows = _build_standup_rows([_item("1", "Mine", assignees=["alice", "bob"])])
        assert rows[0]["assignees"] == "alice, bob"


class TestAssigneeFilterResolution:
    """Normalize assignee behavior between adapter-side and post-fetch filtering."""

    def test_github_me_alias_skips_post_fetch_assignee_filter(self) -> None:
        """GitHub `me`/`@me` should rely on adapter-side filtering, not literal local matching."""
        assert _resolve_post_fetch_assignee_filter("github", "me") is None
        assert _resolve_post_fetch_assignee_filter("github", "@me") is None

    def test_non_me_assignee_is_kept_for_post_fetch_filter(self) -> None:
        """Explicit usernames still apply in local post-fetch filtering."""
        assert _resolve_post_fetch_assignee_filter("github", "djm81") == "djm81"
        assert _resolve_post_fetch_assignee_filter("ado", "me") == "me"


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
        from specfact_backlog.backlog.commands import _post_standup_to_item

        mock = MagicMock(spec=BacklogAdapter)
        mock.add_comment.return_value = True
        item = _item("1", "Task")
        body = _format_standup_comment("X", "Y", "Z")
        ok = _post_standup_to_item(mock, item, body)
        assert ok is True
        mock.add_comment.assert_called_once_with(item, body)

    def test_post_standup_comment_failure_reported(self) -> None:
        """When add_comment returns False, success is False."""
        from specfact_backlog.backlog.commands import _post_standup_to_item

        mock = MagicMock(spec=BacklogAdapter)
        mock.add_comment.return_value = False
        item = _item("1", "Task")
        ok = _post_standup_to_item(mock, item, "Standup text")
        assert ok is False


class TestBacklogDailyCli:
    """CLI: specfact backlog daily."""

    def test_daily_help(self) -> None:
        """Backlog daily subcommand exists."""
        option_names = _get_daily_command_option_names()
        assert len(option_names) > 0

    def test_daily_accepts_sprint_and_iteration_options(self) -> None:
        """Backlog daily has --sprint and --iteration options."""
        option_names = _get_daily_command_option_names()
        assert "--sprint" in option_names
        assert "--iteration" in option_names

    def test_daily_accepts_show_unassigned_and_unassigned_only(self) -> None:
        """Backlog daily has --show-unassigned and --unassigned-only options."""
        option_names = _get_daily_command_option_names()
        assert "--show-unassigned" in option_names
        assert "--no-show-unassigned" in option_names
        assert "--unassigned-only" in option_names

    def test_daily_accepts_blockers_first(self) -> None:
        """Backlog daily has --blockers-first option."""
        option_names = _get_daily_command_option_names()
        assert "--blockers-first" in option_names

    def test_daily_accepts_mode_and_patch_options(self) -> None:
        """Backlog daily supports mode and patch proposal options."""
        option_names = _get_daily_command_option_names()
        assert "--mode" in option_names
        assert "--patch" in option_names

    def test_daily_accepts_search_release_and_id_options(self) -> None:
        """Backlog daily supports global filter parity options."""
        option_names = _get_daily_command_option_names()
        assert "--search" in option_names
        assert "--release" in option_names
        assert "--id" in option_names


class TestIssueIdFilter:
    """Shared issue-id filtering behavior."""

    def test_apply_issue_id_filter_returns_matching_item(self) -> None:
        """When item exists, only matching ID remains."""
        items = [_item("54", "A"), _item("55", "B")]
        filtered = _apply_issue_id_filter(items, "55")
        assert [i.id for i in filtered] == ["55"]

    def test_apply_issue_id_filter_returns_empty_when_not_found(self) -> None:
        """When item ID doesn't exist, result is empty list."""
        items = [_item("54", "A"), _item("55", "B")]
        filtered = _apply_issue_id_filter(items, "999")
        assert filtered == []


class TestDefaultStandupScope:
    """Scenario: Standup view uses default scope when no filters given (6.1)."""

    def test_resolve_standup_options_uses_defaults_when_none(self) -> None:
        """When state/limit/assignee not passed, effective state is open and limit is 20."""
        from specfact_backlog.backlog.commands import _resolve_standup_options

        state, limit, assignee = _resolve_standup_options(None, None, None, None)
        assert state == "open"
        assert limit == 20
        assert assignee is None

    def test_resolve_standup_options_explicit_overrides_defaults(self) -> None:
        """Explicit --state and --limit override defaults."""
        from specfact_backlog.backlog.commands import _resolve_standup_options

        state, limit, assignee = _resolve_standup_options("closed", 10, None, None)
        assert state == "closed"
        assert limit == 10
        assert assignee is None

    def test_resolve_standup_options_any_disables_default_filters(self) -> None:
        """Explicit any/all/* should disable default state/assignee filters."""
        from specfact_backlog.backlog.commands import _resolve_standup_options

        state, limit, assignee = _resolve_standup_options(
            None,
            None,
            None,
            None,
            state_filter_disabled=True,
            assignee_filter_disabled=True,
        )
        assert state is None
        assert limit == 20
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
        from specfact_backlog.backlog.commands import _split_assigned_unassigned

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
        from specfact_backlog.backlog.commands import _split_assigned_unassigned

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

        from specfact_backlog.backlog.commands import _format_sprint_end_header

        end = date(2025, 2, 15)
        header = _format_sprint_end_header(end)
        assert "Sprint ends" in header or "2025-02-15" in header
        assert "days" in header.lower() or "15" in header


class TestBlockersFirstAndOptionalPriority:
    """Scenario: Blockers first and optional priority column (6.5)."""

    def test_standup_rows_blockers_first(self) -> None:
        """When blockers-first, items with non-empty blockers appear first."""
        from specfact_backlog.backlog.commands import _build_standup_rows, _sort_standup_rows_blockers_first

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
        from specfact_backlog.backlog.commands import _build_standup_rows

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

    def test_format_daily_item_detail_omits_comment_block(self) -> None:
        """Interactive detail panel should keep comments out; comments render in dedicated panels."""
        item = _item("1", "Story")
        detail = _format_daily_item_detail(item, comments=["Comment one", "Comment two"])
        assert "Comment one" not in detail
        assert "Comment two" not in detail
        assert "Latest comment" not in detail
        assert "Comments:" not in detail


class TestDailyInteractiveCommentPanels:
    """Daily interactive comment panels should mirror refine-style scoping."""

    def test_default_mode_shows_latest_panel_plus_hint(self) -> None:
        """Without comment-window overrides, show latest comment and hidden-count hint panel."""
        panels = _build_daily_interactive_comment_panels(
            ["Comment one", "Comment two"],
            show_all_provided_comments=False,
            total_comments=2,
        )
        assert len(panels) == 2

    def test_window_mode_shows_all_windowed_panels_plus_omitted_hint(self) -> None:
        """With explicit comment window, render each windowed comment panel and omitted-count hint panel."""
        panels = _build_daily_interactive_comment_panels(
            ["Comment one", "Comment two", "Comment three"],
            show_all_provided_comments=True,
            total_comments=5,
        )
        assert len(panels) == 4


class TestDailyInteractivePostAction:
    """Interactive daily post helpers."""

    def test_navigation_choices_include_post_when_supported(self) -> None:
        """Post action is available when adapter supports comments."""
        choices = _build_daily_navigation_choices(can_post_comment=True)
        assert "Post standup update" in choices

    def test_navigation_choices_omit_post_when_not_supported(self) -> None:
        """Post action is hidden when adapter cannot post comments."""
        choices = _build_daily_navigation_choices(can_post_comment=False)
        assert "Post standup update" not in choices

    def test_build_interactive_post_body_rejects_empty(self) -> None:
        """No text means no post body should be created."""
        assert _build_interactive_post_body(None, "", "   ") is None

    def test_build_interactive_post_body_formats_standup(self) -> None:
        """Any provided standup text creates a valid standup comment body."""
        body = _build_interactive_post_body("Did X", "Do Y", "None")
        assert body is not None
        assert "Standup " in body
        assert "**Yesterday:** Did X" in body
        assert "**Today:** Do Y" in body
        assert "**Blockers:** None" in body


class TestBacklogDailyInteractiveAndExportOptions:
    """CLI: --interactive and --copilot-export options (13.1, 13.2)."""

    def test_daily_help_shows_interactive(self) -> None:
        """Backlog daily has --interactive option."""
        option_names = _get_daily_command_option_names()
        assert "--interactive" in option_names

    def test_daily_help_shows_copilot_export(self) -> None:
        """Backlog daily has --copilot-export option."""
        option_names = _get_daily_command_option_names()
        assert "--copilot-export" in option_names

    def test_daily_help_shows_summarize(self) -> None:
        """Backlog daily has --summarize and --summarize-to options."""
        option_names = _get_daily_command_option_names()
        assert "--summarize" in option_names
        assert "--summarize-to" in option_names

    def test_daily_help_shows_comment_annotations(self) -> None:
        """Backlog daily has --comments/--annotations option for exports."""
        option_names = _get_daily_command_option_names()
        assert "--comments" in option_names
        assert "--annotations" in option_names

    def test_daily_help_shows_comment_window_options(self) -> None:
        """Backlog daily has --first-comments and --last-comments options."""
        option_names = _get_daily_command_option_names()
        assert "--first-comments" in option_names
        assert "--last-comments" in option_names

    def test_daily_help_shows_issue_window_options(self) -> None:
        """Backlog daily has --first-issues and --last-issues options."""
        option_names = _get_daily_command_option_names()
        assert "--first-issues" in option_names
        assert "--last-issues" in option_names


class TestDailyIssueWindowResolution:
    """Daily issue-window behavior should mirror refine semantics."""

    def test_daily_issue_window_applies_first(self) -> None:
        """`--first-issues` keeps the lowest numeric IDs."""
        items = [_item("10", "ten"), _item("2", "two"), _item("7", "seven")]
        windowed = _resolve_daily_issue_window(items, first_issues=2, last_issues=None)
        assert [i.id for i in windowed] == ["2", "7"]

    def test_daily_issue_window_applies_last(self) -> None:
        """`--last-issues` keeps the highest numeric IDs."""
        items = [_item("10", "ten"), _item("2", "two"), _item("7", "seven")]
        windowed = _resolve_daily_issue_window(items, first_issues=None, last_issues=2)
        assert [i.id for i in windowed] == ["7", "10"]

    def test_daily_issue_window_rejects_both(self) -> None:
        """Using both windows should raise a clear validation error."""
        with pytest.raises(ValueError, match="first-issues or --last-issues"):
            _resolve_daily_issue_window([_item("1", "one")], first_issues=1, last_issues=1)


class TestExceptionsFirstAndMode:
    """Exceptions-first and mode defaults for daily standup."""

    def test_split_exception_rows_prioritizes_blockers(self) -> None:
        """Rows with blockers go to exceptions section."""
        rows = [
            {"id": "1", "blockers": ""},
            {"id": "2", "blockers": "Waiting on API"},
            {"id": "3", "blockers": "Needs decision"},
        ]
        exceptions, normal = _split_exception_rows(rows)
        assert [r["id"] for r in exceptions] == ["2", "3"]
        assert [r["id"] for r in normal] == ["1"]

    def test_split_exception_rows_orders_blockers_then_policy_then_aging(self) -> None:
        """Exceptions include blockers, policy failures, and aging/stalled rows in required order."""
        rows = [
            {"id": "1", "blockers": "", "policy_status": "failed"},
            {"id": "2", "blockers": "", "days_stalled": 5},
            {"id": "3", "blockers": "Waiting on dependency"},
            {"id": "4", "blockers": "", "policy_failures": ["dor"]},
            {"id": "5", "blockers": ""},
        ]
        exceptions, normal = _split_exception_rows(rows)
        assert [r["id"] for r in exceptions] == ["3", "1", "4", "2"]
        assert [r["id"] for r in normal] == ["5"]

    def test_mode_kanban_relaxes_default_open_state(self) -> None:
        """Kanban mode removes default open-only filter when state not explicitly provided."""
        effective = _resolve_daily_mode_state(mode="kanban", cli_state=None, effective_state="open")
        assert effective is None

    def test_mode_keeps_explicit_state(self) -> None:
        """Explicit CLI state takes precedence regardless of mode."""
        effective = _resolve_daily_mode_state(mode="kanban", cli_state="closed", effective_state="closed")
        assert effective == "closed"

    def test_patch_proposal_contains_item_ids(self) -> None:
        """Patch proposal includes selected item IDs for review."""
        proposal = _build_daily_patch_proposal([_item("54", "A"), _item("55", "B")], mode="scrum")
        assert "54" in proposal and "55" in proposal
        assert "Patch Proposal" in proposal


class TestDailyFetchLimitResolution:
    """Daily issue-window should evaluate over full candidate set before limit truncation."""

    def test_fetch_limit_kept_without_issue_window(self) -> None:
        """Without issue-window flags, keep effective limit for fetch."""
        assert _resolve_daily_fetch_limit(20, first_issues=None, last_issues=None) == 20

    def test_fetch_limit_removed_with_first_or_last_issue_window(self) -> None:
        """With issue-window flags, fetch full set first."""
        assert _resolve_daily_fetch_limit(20, first_issues=3, last_issues=None) is None
        assert _resolve_daily_fetch_limit(20, first_issues=None, last_issues=3) is None


class TestDailyDisplayLimitResolution:
    """Daily display limit should not truncate issue-window results."""

    def test_display_limit_kept_without_issue_window(self) -> None:
        """Without issue-window flags, keep effective limit for display."""
        assert _resolve_daily_display_limit(20, first_issues=None, last_issues=None) == 20

    def test_display_limit_removed_with_first_or_last_issue_window(self) -> None:
        """With issue-window flags, avoid default display truncation."""
        assert _resolve_daily_display_limit(20, first_issues=25, last_issues=None) is None
        assert _resolve_daily_display_limit(20, first_issues=None, last_issues=25) is None


class TestCommentWindow:
    """Comment window helpers."""

    def test_apply_comment_window_default_full(self) -> None:
        """Default includes all comments."""
        comments = ["c1", "c2", "c3"]
        assert _apply_comment_window(comments) == comments

    def test_apply_comment_window_first(self) -> None:
        """First-comments returns first N comments."""
        comments = ["c1", "c2", "c3"]
        assert _apply_comment_window(comments, first_comments=2) == ["c1", "c2"]

    def test_apply_comment_window_last(self) -> None:
        """Last-comments returns last N comments."""
        comments = ["c1", "c2", "c3"]
        assert _apply_comment_window(comments, last_comments=2) == ["c2", "c3"]

    def test_apply_comment_window_rejects_both_first_and_last(self) -> None:
        """Using both first and last comment windows at once raises ValueError."""
        comments = ["c1", "c2", "c3"]
        with pytest.raises(ValueError):
            _apply_comment_window(comments, first_comments=1, last_comments=1)


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

    def test_summarize_prompt_normalizes_html_description_to_markdown(self) -> None:
        """HTML descriptions (e.g. from ADO) are converted to Markdown-only text."""
        html_body = "<p>Line 1<br />Line 2 &amp; more</p>"
        items = [
            _item(
                "1",
                "HTML body story",
                state="open",
                body_markdown=html_body,
            ),
        ]
        content = _build_summarize_prompt_content(
            items,
            filter_context={"adapter": "ado", "state": "open", "sprint": "—", "assignee": "—", "limit": 10},
            include_value_score=False,
            comments_by_item_id={},
            include_comments=True,
        )
        # Core text is preserved
        assert "Line 1" in content
        assert "Line 2" in content
        assert "more" in content
        # Raw HTML tags and entities are not present
        assert "<p" not in content
        assert "<br" not in content
        assert "&amp;" not in content

    def test_summarize_prompt_normalizes_html_comments_to_markdown(self) -> None:
        """HTML comments are converted to Markdown-only text in the prompt."""
        items = [
            _item(
                "1",
                "Story with html comments",
                state="open",
                body_markdown="Body",
            ),
        ]
        html_comment = "<div>Comment &amp; note<br>next line</div>"
        comments_by_id = {"1": [html_comment]}
        content = _build_summarize_prompt_content(
            items,
            filter_context={"adapter": "ado", "state": "open", "sprint": "—", "assignee": "—", "limit": 10},
            include_value_score=False,
            comments_by_item_id=comments_by_id,
            include_comments=True,
        )
        assert "Comment" in content
        assert "note" in content
        assert "next line" in content
        assert "<div" not in content
        assert "<br" not in content
        assert "&amp;" not in content
