# TDD Evidence: backlog-scrum-01-standup-exceptions-first

## Scope

Delta scope implemented in this pass:

- ADO comments API pagination + `get_comments`
- `backlog daily` comment window options (`--first-comments`, `--last-comments`)
- interactive daily detail comment scoping (latest comment + hidden-count hint)
- `backlog refine --export-to-tmp` comment export context + comment window options

## Pre-Implementation (Expected Failing Tests)

**Status**: Not captured before implementation for this pass (process violation).  
**Recorded at**: 2026-02-10 22:02:36Z

Notes:

- Tests and code were edited in the same implementation window.
- This does not satisfy strict SDD+TDD order (tests failing first before code edits).
- Future changes must capture failing evidence before any production code edits.

## Post-Implementation (Passing Tests)

**Recorded at**: 2026-02-10 22:02:36Z

### Targeted behavior tests

Command:

```bash
hatch run pytest tests/unit/adapters/test_ado_backlog_adapter.py tests/unit/commands/test_backlog_daily.py tests/unit/commands/test_backlog_commands.py -q
```

Result:

- **83 passed** (later rerun after extra assertion: **83/83 passed**; then smart-test run includes these tests and reports **89 passed** in selected set).

### Quality/validation runs

Commands:

```bash
hatch run format
hatch run type-check
hatch run contract-test
hatch run lint
hatch run yaml-lint
hatch run smart-test
openspec validate backlog-scrum-01-standup-exceptions-first --strict
```

Result summary:

- format: pass
- type-check: pass (0 errors, warnings present in repo baseline)
- contract-test: pass
- lint: pass
- yaml-lint: pass
- smart-test: pass (selected unit set)
- openspec strict validation: pass

## Incremental Delta: Refine Preview Comment Scope (2026-02-10)

### Pre-Implementation (Expected Failure Captured)

**Recorded at**: 2026-02-10 22:10:49Z

Command:

```bash
hatch run pytest tests/unit/commands/test_backlog_commands.py -k "RefineCommentWindowResolution" -v
```

Result:

- **failed during collection** (expected before implementation):
  - `ImportError: cannot import name '_resolve_refine_export_comment_window'`

### Post-Implementation (Passing)

**Recorded at**: 2026-02-10 22:10:49Z

Commands:

```bash
hatch run pytest tests/unit/commands/test_backlog_commands.py -k "RefineCommentWindowResolution or BuildRefineExportContent" -v
hatch run pytest tests/unit/commands/test_backlog_commands.py tests/unit/commands/test_backlog_daily.py tests/unit/adapters/test_ado_backlog_adapter.py -q
```

Result:

- Targeted refine tests: **6 passed**
- Regression set: **87 passed**

## Incremental Delta: Refine Preview UX Feedback (2026-02-10)

### Pre-Implementation (Expected Failure Captured)

**Recorded at**: 2026-02-10 22:21:17Z

Command:

```bash
hatch run pytest tests/unit/commands/test_backlog_commands.py -k "RefinePreviewCommentUx" -v
```

Result:

- **failed during collection** (expected before implementation):
  - `ImportError: cannot import name '_build_comment_fetch_progress_description'`

### Post-Implementation (Passing)

**Recorded at**: 2026-02-10 22:21:17Z

Commands:

```bash
hatch run pytest tests/unit/commands/test_backlog_commands.py -k "RefinePreviewCommentUx or RefineCommentWindowResolution" -v
hatch run pytest tests/unit/commands/test_backlog_commands.py tests/unit/commands/test_backlog_daily.py tests/unit/adapters/test_ado_backlog_adapter.py -q
```

Result:

- Targeted refine UX tests: **6 passed**
- Regression set: **89 passed**

## Incremental Delta: Refine Issue Window Controls (2026-02-10)

### Pre-Implementation (Expected Failure Captured)

**Recorded at**: 2026-02-10 22:25:53Z

Command:

```bash
hatch run pytest tests/unit/commands/test_backlog_commands.py -k "RefineIssueWindow" -v
```

Result:

- **failed during collection** (expected before implementation):
  - `ImportError: cannot import name '_apply_issue_window'`

### Post-Implementation (Passing)

**Recorded at**: 2026-02-10 22:25:53Z

Commands:

```bash
hatch run pytest tests/unit/commands/test_backlog_commands.py -k "RefineIssueWindow" -v
hatch run pytest tests/unit/commands/test_backlog_commands.py tests/unit/commands/test_backlog_daily.py tests/unit/adapters/test_ado_backlog_adapter.py -q
```

Result:

- Targeted issue-window tests: **3 passed**
- Regression set: **92 passed**

## Incremental Delta: Refine Issue Window Ordering Fix (2026-02-10)

### Pre-Implementation (Expected Failure Captured)

**Recorded at**: 2026-02-10 22:28:42Z

Command:

```bash
hatch run pytest tests/unit/commands/test_backlog_commands.py -k "RefineIssueWindow" -v
```

Result:

- **2 tests failed** (expected before ordering fix):
  - `test_apply_issue_window_first_issues`
  - `test_apply_issue_window_last_issues`
- Failure showed current behavior using input order instead of numeric ID order.

### Post-Implementation (Passing)

**Recorded at**: 2026-02-10 22:28:42Z

Commands:

```bash
hatch run pytest tests/unit/commands/test_backlog_commands.py -k "RefineIssueWindow" -v
hatch run pytest tests/unit/commands/test_backlog_commands.py tests/unit/commands/test_backlog_daily.py tests/unit/adapters/test_ado_backlog_adapter.py -q
```

Result:

- Targeted issue-window tests: **3 passed**
- Regression set: **92 passed**

## Incremental Delta: No-Comments Preview Hint (2026-02-10)

### Pre-Implementation (Expected Failure Captured)

**Recorded at**: 2026-02-10 22:33:57Z

Command:

```bash
hatch run pytest tests/unit/commands/test_backlog_commands.py -k "RefinePreviewCommentUx" -v
```

Result:

- **failed during collection** (expected before implementation):
  - `ImportError: cannot import name '_build_refine_preview_comment_empty_panel'`

### Post-Implementation (Passing)

**Recorded at**: 2026-02-10 22:33:57Z

Commands:

```bash
hatch run pytest tests/unit/commands/test_backlog_commands.py -k "RefinePreviewCommentUx" -v
hatch run pytest tests/unit/commands/test_backlog_commands.py tests/unit/commands/test_backlog_daily.py tests/unit/adapters/test_ado_backlog_adapter.py -q
```

Result:

- Targeted preview UX tests: **3 passed**
- Regression set: **93 passed**

## Incremental Delta: Write-Mode Prompt Comment Context (2026-02-10)

### Pre-Implementation (Expected Failure Captured)

**Recorded at**: 2026-02-10 22:42:10Z

Command:

```bash
hatch run pytest tests/unit/backlog/test_ai_refiner.py -k "includes_comments_when_provided or mentions_no_comments_when_empty" -v
```

Result:

- **2 tests failed** (expected before implementation):
  - `test_generate_refinement_prompt_includes_comments_when_provided`
  - `test_generate_refinement_prompt_mentions_no_comments_when_empty`
- Failure root cause: `generate_refinement_prompt()` did not accept `comments` argument.

### Post-Implementation (Passing)

**Recorded at**: 2026-02-10 22:42:10Z

Commands:

```bash
hatch run pytest tests/unit/backlog/test_ai_refiner.py -k "includes_comments_when_provided or mentions_no_comments_when_empty" -v
hatch run pytest tests/unit/backlog/test_ai_refiner.py tests/unit/commands/test_backlog_commands.py tests/unit/commands/test_backlog_daily.py tests/unit/adapters/test_ado_backlog_adapter.py -q
```

Result:

- Targeted AI refiner comment-context tests: **2 passed**
- Regression set: **106 passed**

## Incremental Delta: Refine Export Copilot Instruction Header (2026-02-10)

### Pre-Implementation (Expected Failure Captured)

**Recorded at**: 2026-02-10 22:50:31Z

Command:

```bash
hatch run pytest tests/unit/commands/test_backlog_commands.py -k "BuildRefineExportContent" -v
```

Result:

- **2 tests failed** (expected before implementation):
  - `test_refine_export_includes_comments_when_available`
  - `test_refine_export_places_instructions_before_first_item`
- Failure root cause: export did not include a top-level instruction block.

### Post-Implementation (Passing)

**Recorded at**: 2026-02-10 22:50:31Z

Commands:

```bash
hatch run pytest tests/unit/commands/test_backlog_commands.py -k "BuildRefineExportContent" -v
hatch run pytest tests/unit/backlog/test_ai_refiner.py tests/unit/commands/test_backlog_commands.py tests/unit/commands/test_backlog_daily.py tests/unit/adapters/test_ado_backlog_adapter.py -q
```

Result:

- Targeted export-content tests: **3 passed**
- Regression set: **107 passed**

## Incremental Delta: Export Instruction Parity with Interactive Mode (2026-02-10)

### Pre-Implementation (Expected Failure Captured)

**Recorded at**: 2026-02-10 22:55:51Z

Command:

```bash
hatch run pytest tests/unit/commands/test_backlog_commands.py -k "BuildRefineExportContent" -v
```

Result:

- **2 tests failed** (expected before implementation):
  - `test_refine_export_includes_comments_when_available` (missing full interactive-equivalent rule text)
  - `test_refine_export_includes_template_guidance_for_items` (missing per-item template guidance fields)

### Post-Implementation (Passing)

**Recorded at**: 2026-02-10 22:55:51Z

Commands:

```bash
hatch run pytest tests/unit/commands/test_backlog_commands.py -k "BuildRefineExportContent" -v
hatch run pytest tests/unit/backlog/test_ai_refiner.py tests/unit/commands/test_backlog_commands.py tests/unit/commands/test_backlog_daily.py tests/unit/adapters/test_ado_backlog_adapter.py -q
```

Result:

- Targeted export-content tests: **4 passed**
- Regression set: **108 passed**

## Incremental Delta: Daily Assignee Visibility + GitHub `me` Filter (2026-02-11)

### Pre-Implementation (Expected Failure Captured)

**Recorded at**: 2026-02-11 00:12:34Z

Command:

```bash
hatch run pytest tests/unit/commands/test_backlog_daily.py -k "row_includes_assignees_for_table_rendering or AssigneeFilterResolution" -q
```

Result:

- **failed during collection** (expected before implementation):
  - `ImportError: cannot import name '_resolve_post_fetch_assignee_filter'`

### Post-Implementation (Passing)

**Recorded at**: 2026-02-11 00:12:34Z

Commands:

```bash
hatch run pytest tests/unit/commands/test_backlog_daily.py -k "row_includes_assignees_for_table_rendering or AssigneeFilterResolution" -q
hatch run pytest tests/unit/adapters/test_github_backlog_adapter.py -k "me_assignee or assignee_filter" -q
hatch run pytest tests/unit/commands/test_backlog_daily.py tests/unit/commands/test_backlog_commands.py tests/unit/adapters/test_github_backlog_adapter.py tests/unit/adapters/test_ado_backlog_adapter.py -q
```

Result:

- Targeted daily tests: **3 passed**
- Targeted GitHub adapter tests: **2 passed**
- Regression set: **109 passed**

## Incremental Delta: Daily Issue Window Parity with Refine (2026-02-11)

### Pre-Implementation (Expected Failure Captured)

**Recorded at**: 2026-02-11 00:24:07Z

Command:

```bash
hatch run pytest tests/unit/commands/test_backlog_daily.py -k "issue_window" -q
```

Result:

- **failed during collection** (expected before implementation):
  - `ImportError: cannot import name '_resolve_daily_issue_window'`

### Post-Implementation (Passing)

**Recorded at**: 2026-02-11 00:24:07Z

Commands:

```bash
hatch run pytest tests/unit/commands/test_backlog_daily.py -k "issue_window" -q
hatch run pytest tests/unit/commands/test_backlog_daily.py tests/unit/commands/test_backlog_commands.py tests/unit/adapters/test_github_backlog_adapter.py tests/unit/adapters/test_ado_backlog_adapter.py -q
```

Result:

- Targeted issue-window tests: **4 passed**
- Regression set: **113 passed**

## Incremental Delta: Daily Issue Window Before Pre-Limit Truncation (2026-02-11)

### Pre-Implementation (Expected Failure Captured)

**Recorded at**: 2026-02-11 00:31:27Z

Command:

```bash
hatch run pytest tests/unit/commands/test_backlog_daily.py -k "DailyFetchLimitResolution" -q
```

Result:

- **failed during collection** (expected before implementation):
  - `ImportError: cannot import name '_resolve_daily_fetch_limit'`

### Post-Implementation (Passing)

**Recorded at**: 2026-02-11 00:31:27Z

Commands:

```bash
hatch run pytest tests/unit/commands/test_backlog_daily.py -k "DailyFetchLimitResolution or DailyIssueWindowResolution" -q
hatch run pytest tests/unit/commands/test_backlog_daily.py tests/unit/commands/test_backlog_commands.py tests/unit/adapters/test_github_backlog_adapter.py tests/unit/adapters/test_ado_backlog_adapter.py -q
```

Result:

- Targeted fetch-limit/issue-window tests: **5 passed**
- Regression set: **115 passed**

## Incremental Delta: Interactive Comment Window Override in Daily (2026-02-11)

### Pre-Implementation (Expected Failure Captured)

**Recorded at**: 2026-02-11 00:36:11Z

Command:

```bash
hatch run pytest tests/unit/commands/test_backlog_daily.py -k "honors_explicit_comment_window_in_interactive" -q
```

Result:

- **1 test failed** (expected before implementation):
  - `TypeError: _format_daily_item_detail() got an unexpected keyword argument 'show_all_provided_comments'`

### Post-Implementation (Passing)

**Recorded at**: 2026-02-11 00:36:11Z

Commands:

```bash
hatch run pytest tests/unit/commands/test_backlog_daily.py -k "honors_explicit_comment_window_in_interactive or shows_latest_comment_only_with_hint" -q
hatch run pytest tests/unit/commands/test_backlog_daily.py tests/unit/commands/test_backlog_commands.py tests/unit/adapters/test_github_backlog_adapter.py tests/unit/adapters/test_ado_backlog_adapter.py -q
```

Result:

- Targeted interactive comment tests: **2 passed**
- Regression set: **116 passed**

## Incremental Delta: Daily Interactive Comment Panel Formatting (2026-02-11)

### Pre-Implementation (Expected Failure Captured)

**Recorded at**: 2026-02-11 00:44:03Z

Command:

```bash
hatch run pytest tests/unit/commands/test_backlog_daily.py -k "DailyInteractiveCommentPanels or omits_comment_block" -q
```

Result:

- **failed during collection** (expected before implementation):
  - `ImportError: cannot import name '_build_daily_interactive_comment_panels'`

### Post-Implementation (Passing)

**Recorded at**: 2026-02-11 00:44:03Z

Commands:

```bash
hatch run pytest tests/unit/commands/test_backlog_daily.py -k "DailyInteractiveCommentPanels or omits_comment_block" -q
hatch run pytest tests/unit/commands/test_backlog_daily.py tests/unit/commands/test_backlog_commands.py tests/unit/adapters/test_github_backlog_adapter.py tests/unit/adapters/test_ado_backlog_adapter.py -q
```

Result:

- Targeted panel-format tests: **3 passed**
- Regression set: **117 passed**

## Incremental Delta: Daily Global Filter Parity (`--search`, `--release`, `--id`) (2026-02-11)

### Pre-Implementation (Expected Failure Captured)

**Recorded at**: 2026-02-11 01:02:19Z

Command:

```bash
hatch run pytest tests/unit/commands/test_backlog_daily.py -k "search_release_and_id_options or IssueIdFilter" -q
```

Result:

- **failed during collection** (expected before implementation):
  - `ImportError: cannot import name '_apply_issue_id_filter'`

### Post-Implementation (Passing)

**Recorded at**: 2026-02-11 01:02:19Z

Commands:

```bash
hatch run pytest tests/unit/commands/test_backlog_daily.py -k "search_release_and_id_options or IssueIdFilter" -q
hatch run pytest tests/unit/commands/test_backlog_daily.py tests/unit/commands/test_backlog_commands.py tests/unit/adapters/test_github_backlog_adapter.py tests/unit/adapters/test_ado_backlog_adapter.py -q
```

Result:

- Targeted global-filter parity tests: **3 passed**
- Regression set: **120 passed**

## Incremental Delta: Exceptions-First Ordering + Daily Mode/Patch Completion (2026-02-11)

### Pre-Implementation (Expected Failure Captured)

**Recorded at**: 2026-02-11 01:14:00Z

Command:

```bash
hatch run pytest tests/unit/commands/test_backlog_daily.py -k "orders_blockers_then_policy_then_aging" -q
```

Result:

- **1 test failed** (expected before implementation):
  - `test_split_exception_rows_orders_blockers_then_policy_then_aging`
- Failure showed only blocker rows were classified as exceptions; policy/aging rows were not included.

### Post-Implementation (Passing)

**Recorded at**: 2026-02-11 01:15:00Z

Commands:

```bash
hatch run pytest tests/unit/commands/test_backlog_daily.py -k "ExceptionsFirstAndMode" -q
hatch run pytest tests/unit/commands/test_backlog_daily.py tests/unit/commands/test_backlog_commands.py tests/unit/adapters/test_github_backlog_adapter.py tests/unit/adapters/test_ado_backlog_adapter.py -q
```

Result:

- Targeted exceptions/mode/patch tests: **5 passed**
- Regression set: **126 passed**

## Incremental Delta: Interactive Daily Post Action on Selected Story (2026-02-11)

### Pre-Implementation (Expected Failure Captured)

**Recorded at**: 2026-02-11 01:31:00Z

Command:

```bash
hatch run pytest tests/unit/commands/test_backlog_daily.py -k "InteractivePostAction" -q
```

Result:

- **failed during collection** (expected before implementation):
  - `ImportError: cannot import name '_build_daily_navigation_choices'`

### Post-Implementation (Passing)

**Recorded at**: 2026-02-11 01:33:00Z

Commands:

```bash
hatch run pytest tests/unit/commands/test_backlog_daily.py -k "InteractivePostAction" -q
hatch run pytest tests/unit/commands/test_backlog_daily.py tests/unit/commands/test_backlog_commands.py -q
```

Result:

- Targeted interactive post tests: **4 passed**
- Regression set (`daily` + `backlog commands`): **97 passed**
