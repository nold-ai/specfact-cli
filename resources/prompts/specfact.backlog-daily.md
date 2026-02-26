---
description: "Daily standup and sprint review with story-by-story walkthrough"
---

# SpecFact Daily Standup Command

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

Run a daily standup view and optional interactive walkthrough of backlog items (GitHub Issues, Azure DevOps work items) with the DevOps team: list items in scope, review story-by-story, highlight current focus, surface issues or open questions, and allow adding discussion notes as annotation comments on the issue.

**When to use:** Daily standup, sprint review, quick status sync with the team.

**Quick:** `/specfact.daily` or `/specfact.backlog-daily` with optional adapter and filters. From a clone, org/repo or org/project are auto-detected from git remote.

## Parameters

### Required

- `ADAPTER` - Backlog adapter name (github, ado, etc.)

### Adapter Configuration (same as backlog-refine)

**GitHub:** `--repo-owner`, `--repo-name`, `--github-token` (optional).  
**Azure DevOps:** `--ado-org`, `--ado-project`, `--ado-team` (optional), `--ado-base-url`, `--ado-token` (optional).

When run from a **clone**, org/repo or org/project are inferred from `git remote get-url origin`; no need to pass them unless overriding.

### Filters

- `--state STATE` - Filter by state (e.g. open, Active). Use `--state any` to disable state filtering.
- `--assignee USERNAME` or `--assignee me` - Filter by assignee. Use `--assignee any` to disable assignee filtering.
- `--search QUERY` - Provider-specific search query
- `--release RELEASE` - Filter by release identifier
- `--id ISSUE_ID` - Filter to one exact backlog item ID
- `--sprint SPRINT` / `--iteration PATH` - Filter by sprint/iteration (e.g. `current`)
- `--limit N` - Max items (default 20)
- `--first-issues N` / `--last-issues N` - Optional issue window (oldest/newest by numeric ID, mutually exclusive)
- `--blockers-first` - Sort items with blockers first
- `--show-unassigned` / `--unassigned-only` - Include or show only unassigned items

### Daily-Specific Options

- `--interactive` - Step-by-step review: select items with arrow keys, view full detail (refine-like) and **existing comments** on each issue
- `--copilot-export PATH` - Write summarized progress per story to a file for Copilot slash-command use
- `--summarize` - Output a prompt (instruction + filter context + standup data) to **stdout** for Copilot or slash command to generate a standup summary
- `--summarize-to PATH` - Write the same summarize prompt to a **file**
- `--comments` / `--annotations` - Include descriptions and comments in `--copilot-export` and summarize output
- `--first-comments N` / `--last-comments N` - Optional comment window for export/summarize outputs (`--comments`); default includes all comments
- `--suggest-next` - In interactive mode, show suggested next item by value score
- `--post` with `--yesterday`, `--today`, `--blockers` - Post a standup comment to the first item's issue (when adapter supports comments)
- Interactive navigation action `Post standup update` - Post yesterday/today/blockers to the currently selected story during `--interactive` walkthrough

## Workflow

### Step 1: Run Daily Standup

Execute the CLI with adapter and optional filters:

```bash
specfact backlog daily $ADAPTER [--state open] [--sprint current] [--assignee me] [--limit 20]
```

Or use the slash command with arguments: `/specfact.backlog-daily --adapter ado --sprint current`

**What you see:** A standup table (assigned items) and a "Pending / open for commitment" table (unassigned items in scope). Each row shows ID, title, status, last updated, and optional yesterday/today/blockers from the item body.

### Step 2: Interactive Story-by-Story Review (with DevOps team)

When the user runs **`--interactive`** (or the slash command drives an interactive flow):

1. **For each story** (one at a time):
   - **Present** the item: ID, title, status, assignees, last updated, description, acceptance criteria, standup fields (yesterday/today/blockers), and the **latest existing comment** (when the adapter supports fetching comments).
   - **Interactive comment scope**: If older comments exist, explicitly mention the count of hidden comments and guide users to export options for full context.
   - **Highlight current focus**: What is the team member working on? What is the next intended step?
   - **Surface issues or open questions**: Blockers, ambiguities, dependencies, or decisions needed.
   - **Allow discussion notes**: If the team agrees, suggest or add a **comment** on the issue (e.g. "Standup YYYY-MM-DD: …" or "Discussion: …") so the discussion is captured as an annotation. Only add comments when the user explicitly approves (e.g. "add that as a comment").
   - If in CLI interactive navigation, use **Post standup update** to write the note to the selected story directly.
   - **Move to next** only when the team is done with this story (e.g. "next", "done").

2. **Rules**:
   - Do not update the backlog item body or title unless the user asks for a refinement (use `specfact backlog refine` for that).
   - Comments are for **discussion notes** and standup updates; keep them short and actionable.
   - If the adapter does not support comments, report that clearly and skip adding comments.

3. **Navigation**: After each story, offer "Next story", "Previous story", "Back to list", "Exit" (or equivalent) so the team can move through the list without re-running the command.

### Step 3: Generate Standup Summary (optional)

When the user has run `specfact backlog daily ... --summarize` or `--summarize-to PATH`, the output is a **prompt** containing:

- A short instruction: generate a concise daily standup summary from the following data.
- Filter context (adapter, state, sprint, assignee, limit).
- Per-item data (same as `--copilot-export`: ID, title, status, assignees, last updated, progress, blockers).

**Use this output** by pasting it into Copilot or invoking the slash command `specfact.daily` with this context, so the AI can produce a short narrative summary (e.g. "Today's standup: 3 in progress, 1 blocked, 2 pending commitment …").

## Comments on Issues

- **Interactive detail view** shows only the **latest comment** plus a hint when additional comments exist, to keep standup readable.
- **Full comment context**: use `--copilot-export <path> --comments` or `--summarize --comments` (optional `--first-comments N` / `--last-comments N`) to include full or scoped comment history.
- **Adding comments**: When the team agrees to record a discussion note or standup update, add it as a comment on the issue (via `--post` for first-item standup lines or interactive **Post standup update** for selected stories). Do not invent comments; only suggest or add when the user approves.

## CLI Enforcement

- Execute `specfact backlog daily` (or equivalent) first; use its output as context.
- Use `--interactive` for story-by-story walkthrough; use `--summarize` or `--summarize-to` when a standup summary prompt is needed.
- Use `--copilot-export` when you need a file of item summaries for reference during standup.

## Output Contract

- This command does not support `--import-from-tmp`; do not invent a tmp import schema.
- Do not instruct Copilot to produce `## Item N:` blocks or `**ID**`/`**Body**` tmp artifacts for this command.
- If you write `--copilot-export` or `--summarize-to` artifacts, keep item sections and IDs unchanged from CLI output.

## Context

{ARGS}
