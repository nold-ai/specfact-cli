# Design: Daily standup and progress support

## Default standup scope and config

- **Default state**: When user does not pass `--state`, apply a default so closed/done items are excluded (e.g. `open` for GitHub, "Active" or equivalent for ADO). Built-in default: `open`; overridable by config or env (e.g. `SPECFACT_STANDUP_STATE`, or `standup.default_state` in `.specfact/standup.yaml`).
- **Default assignee**: Optional default `assignee=me` (current user when resolvable from adapter or env) so "my items" are shown by default. Config: `SPECFACT_STANDUP_ASSIGNEE` or `standup.default_assignee`; when unset, no default assignee (show all in scope).
- **Default limit**: Cap number of items (e.g. 20 or 30) for scannable output. Built-in default: e.g. 20; overridable by config or env (e.g. `SPECFACT_STANDUP_LIMIT`, or `standup.limit` in config file).
- **Config file**: Optional `.specfact/standup.yaml` (or under `SPECFACT_CONFIG_DIR`) with keys such as `default_state`, `default_assignee`, `limit`, `sprint` (current or name), `show_unassigned` (bool). Env vars override config file; CLI options override both.
- **Kanban**: For Kanban, teams can omit iteration/sprint and rely on state + limit; unassigned items represent pullable work.

## Current iteration/sprint

- **Adapter support**: Use existing `iteration` / `sprint` fields on `BacklogItem` and existing `_apply_filters(..., iteration=..., sprint=...)`. For "current" sprint, adapter or a small helper resolves "current" to the active iteration (e.g. ADO team's current iteration; GitHub may use project board or labels).
- **daily command**: Add `--iteration` and `--sprint` to `specfact backlog daily` (same as in `refine`). Support value `current` when adapter can resolve it; otherwise use literal value. Config can set `sprint: current` for standup-only default.
- **Sprint/iteration context**: When `--sprint current` or config sprint is in use and the adapter (or config) provides an iteration/sprint end date, display it in the standup view (e.g. header or first line: "Sprint ends: YYYY-MM-DD (N days)"). If the adapter does not provide it, support optional config (e.g. `standup.sprint_end_date` or `iteration_end_date`) for manual override. No new adapter contract required if using existing iteration/sprint metadata or config.
- **Fallback**: If adapter does not provide iteration/sprint or "current" cannot be resolved, omit iteration/sprint filter and document in help; no crash.

## Unassigned/pending items

- **Definition**: Items in the same scope (state, iteration/sprint) whose `assignees` is empty or None.
- **Presentation**: Two options (implement one or both):
  - **Separate table**: After the main "Daily standup" (assigned) table, render a second table titled e.g. "Pending / open for commitment" with unassigned items (same columns or subset: ID, Title, Status, Last updated). Omit section when there are no unassigned items.
  - **Parameter**: `--unassigned` or `--show-pending` to include the unassigned table; default can be true for standup (show both) or false (only assigned). `--unassigned-only` shows only unassigned items (single table).
- **Scope**: Unassigned items use the same filters (state, iteration, sprint, labels) so they are "in sprint / open but not yet assigned."
- **Order**: Keep assigned table first (primary standup), unassigned second (commitment/pick-up).

## Blockers and time-critical

- **Blockers prominence**: Optionally sort the standup table so rows with non-empty Blockers appear first, or add a `--blockers-first` flag, so time-critical issues are visible at a glance.

## Value / priority (optional)

- When available on `BacklogItem`, show priority (or `business_value` / `value_points`) in the daily table or via a config option, to support value-driven (SAFe/WSJF) focus.

## Bridge adapter integration

- **Standup view**: Reads from existing OpenSpec change proposals and/or backlog adapter data (same sources as `specfact sync bridge` and backlog commands). No new adapter contract; reuse existing list/fetch APIs.
- **Post standup comment**: When user opts in, use existing GitHub (and optionally ADO) adapter to add a comment to the linked issue. GitHub: use Issues API `POST /repos/{owner}/{repo}/issues/{issue_number}/comments` with standup body. ADO: use Work Item Comments API if available; otherwise document as future extension.
- **Adapter capability**: Adapters that support "post comment" expose a method (e.g. `post_comment(issue_id, body)`) or equivalent; standup command calls it when adapter supports it and user opts in. Read-only or unsupported adapters return a clear "not supported" so the CLI does not attempt to post.

## Sequence (post standup comment)

```text
User → specfact standup --post-standup --standup-text "Yesterday: X. Today: Y. Blockers: Z"
  → CLI resolves change proposal → Source Tracking → issue number + repo
  → CLI gets adapter for repo (e.g. GitHub)
  → If adapter supports post_comment: adapter.post_comment(issue_number, formatted_body)
  → GitHub API: POST .../issues/{n}/comments
  → CLI reports success or failure
```

## Contract enforcement

- New public functions (e.g. standup view builder, comment poster) shall have @icontract and @beartype.
- Adapter interface extension (post_comment) optional with default "not supported" to keep backward compatibility.

## Fallback / offline

- Standup view is read-only from local/cached data; no network required for view-only.
- Post comment requires network and auth; failure (rate limit, auth) is reported; no silent swallow.

## Alignment with existing sync bridge

- Existing `specfact sync bridge --add-progress-comment` and `--track-code-changes` already add progress comments to GitHub issues. Standup comment can reuse or extend that path (e.g. standup format as a variant of progress comment) to avoid duplicate comment-posting logic. Standup/progress is exposed under the backlog command group as `specfact backlog daily` (no top-level standup or scrum command).

## Interactive step-by-step review

- **Trigger**: `specfact backlog daily --interactive` (or equivalent flag). Same scope as non-interactive daily (state, iteration/sprint, assignee, limit, unassigned) so items shown are the same as the table view.
- **Selection UI**: Use questionary (or equivalent) for arrow-key selection, consistent with existing template field mapping (e.g. `backlog_commands.py` questionary.select). Choices: one per backlog item in scope, label format e.g. `{id} - {title} [{status}] ({assignee})` so user can pick an item to inspect.
- **Detail view**: When user selects an item, display full details comparable to `specfact backlog refine <item-id>`: ID, title, status, assignees, last updated, description/body, acceptance criteria, story points, business value, priority (when available), standup fields (yesterday/today/blockers). Fetch and display **existing comments** from the adapter (e.g. `_get_issue_comments` / `_get_work_item_comments`); highlight blocked status if blockers non-empty.
- **Navigation**: After showing detail, present choices: "Next story", "Previous story", "Back to list", "Exit". "Next/Previous" move to next/previous item in current ordered list without re-opening the full menu; "Back to list" returns to the item selector; "Exit" ends the command.
- **Next-best-item suggestion**: When adapter or BacklogItem provides story_points, business_value, priority: compute a value score for pending (e.g. todo/unassigned) items, e.g. `value_score = business_value / (story_points * priority)` (guard against zero). Optionally show "Suggested next: <id> - <title> (score: X)" in the detail view or in the list. Config or flag to enable/disable (e.g. `--suggest-next` or standup config).
- **Sprint goal alignment**: When sprint goal is provided by adapter or config (e.g. `standup.sprint_goal` or adapter metadata), optional hint in interactive view (e.g. "Sprint goal: …") so user can align; no editing of sprint goal. If not available, omit.
- **Contract**: New public helpers (e.g. interactive walkthrough, detail renderer) shall have @icontract and @beartype. Reuse existing refine and comment-fetch paths where possible.

## Export to file for Copilot

- **Trigger**: `specfact backlog daily --copilot-export <path>` (or `--export-copilot <path>`). Same scope as daily (current iteration/sprint, active/blocked/todo). When both `--interactive` and `--copilot-export` are given, export can run after interactive session or in addition; design choice: export runs on same fetched list (no need to re-fetch).
- **Content**: One section per backlog item in scope. Per item include: ID, title, status, assignee(s), last updated, short progress summary (standup fields if present), blockers, and optionally value score / priority / story points so Copilot can assist with "which to pick next" and "what's blocked". Format: Markdown with clear headings (e.g. `## <id> - <title>`) and bullet points for quick scanning and Copilot slash-command use.
- **Purpose**: File is for use during standup with Copilot (e.g. paste or reference in slash command) to summarize current progress and next steps per story; complementary to the backlog, not a replacement.
- **Contract**: Export builder function shall have @icontract and @beartype; idempotent write to file (overwrite or configurable).

## Value score and "next to pick" (optional)

- **Formula**: When story_points, business_value, and priority are available, use e.g. `value_score = business_value / max(1, story_points * priority)` so higher score = higher value per unit effort/priority. Use for (1) optional column in daily table, (2) optional "suggested next" in interactive view, (3) optional line in Copilot export.
- **When data missing**: Omit score or column; no fake values. Document which adapters/fields provide the data.

## Out of scope / Future work (not in this change)

- **Stale / at-risk items** (e.g. "no update in N days"): Possible future "gaps" enhancement; not a requirement in this change. Many teams get what they need from "last updated" + blockers; no explicit "at risk" flag or threshold in scope.
- **Sprint goal**: Not displayed or edited; when provided by adapter/config, used only for optional alignment hint in interactive/export. Users see sprint goal in their board/sprint settings.
- **Structured "blocked by"**: Only free-text blockers (standup blockers field) are in scope. BacklogItem has no first-class `blocked_by` (link to another issue). Acceptable for typical standups; structured dependency links are out of scope.
- **Replacement for backlog**: Interactive and export are complementary aids; they do not replace the backlog or board.
