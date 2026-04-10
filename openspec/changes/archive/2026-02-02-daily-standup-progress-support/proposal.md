# Change: Daily standup and progress support

## Why

Bridge comments and sync already support exporting/updating change proposals and issues. For daily standup there is no structured "standup" view that aggregates my items, recent activity, and blockers; progress/standup notes are not first-class (e.g. yesterday/today/blockers format) that could be pushed to issue comments. Teams duplicate standup info in tools; SpecFact can surface progress from OpenSpec/bridge and optionally publish to GitHub/ADO so standup updates are visible where the team works. Daily standups should focus on current iteration/sprint, unassigned work for commitment, and early visibility of blockers and time-critical items so DevOps teams can deliver the right features.

## What Changes

- **NEW**: Add a lightweight standup/progress view under the backlog command group: list my change proposals or backlog items (by assignee or filter), with last-updated and status; optional one-line summary for yesterday/today/blockers from proposal or linked issue body. Expose as `specfact backlog daily` (no top-level `specfact standup`).
- **NEW**: Optional mode to post standup summary as a comment on linked issues via `specfact backlog daily` (e.g. `--post`) or reuse of `specfact sync bridge --add-progress-comment` with standup format (e.g. GitHub issue comment).
- **NEW**: Default standup scope for meaningful daily standups: default state filter (e.g. open/active so closed items are excluded), optional default assignee (e.g. current user / "me" when resolvable), and default limit (e.g. 20–30 items). Configurable via environment variables and/or `.specfact/standup.yaml` (or equivalent) so teams can tailor defaults.
- **NEW**: Current iteration/sprint focus: when the adapter supports iteration or sprint (e.g. GitHub Projects, ADO iteration), allow filtering or scoping the standup view to the current iteration/sprint so "new items to start" in the sprint are visible and can be committed to during standup.
- **NEW**: Unassigned/pending items view: show items with no assignee (backfill, open sprint, or pending) in a separate table or via an additional parameter (e.g. `--unassigned` / `--pending`) so the team can discuss and commit to picking them up during standup, alongside assigned "in progress" items.
- **EXTEND**: When viewing current iteration/sprint, show sprint/iteration end date when provided by adapter or config so teams see "days left in sprint"; optionally surface priority or value in the standup view for value-driven (e.g. SAFe) teams.
- **EXTEND**: Bridge/adapters: support posting comment to linked issue when adapter supports it (e.g. GitHub).
- **EXTEND**: Documentation (agile-scrum-workflows, devops-adapter-integration) for daily standup with SpecFact, including default scope, iteration/sprint, unassigned items, Kanban vs Scrum/SAFe usage, and time-critical/blockers focus.
- **NEW**: Interactive step-by-step review: `specfact backlog daily --interactive` (or equivalent) presents backlog items in the current scope via arrow-key selection (e.g. questionary); user selects an item to see full details (as in `specfact backlog refine` per item), including progress, existing comments, and optional "next best item" suggestion based on value/priority/complexity (e.g. business value / (story points × priority)) for pending items. Complementary to the backlog; no replacement for the backlog itself.
- **NEW**: Export to file for Copilot: option (e.g. `--copilot-export <path>`) to write a summarized view of each story (current iteration/sprint, active/blocked/todo) to a file for use with Copilot slash-command interactive review during standup—assisting next steps and summarizing progress per story for team discussion. Format is Markdown or team-friendly so Copilot can assist with informed feedback and decision-making (blocked items, which item to pick next).
- **NEW**: Project backlog context: store non-sensitive adapter context (org, project per adapter) in the repo so users do not have to pass `--repo-owner`/`--repo-name` or `--ado-org`/`--ado-project` every time after authenticating once. Use `.specfact/backlog.yaml` (no tokens, no users); resolution order: CLI args > env (e.g. `SPECFACT_GITHUB_REPO_OWNER`) > file. Applies to all backlog commands (daily, refine, sync bridge, etc.).
- **CLARIFY**: Interactive detail view shows **existing comments** annotated to each issue (fetched via adapter when supported; e.g. GitHub issue comments, ADO work item discussion). Document in tutorial and spec.
- **NEW**: Slash-command prompt for daily standup: add `resources/prompts/specfact.backlog-daily.md` (analogous to `specfact.backlog-refine.md`) so teams can run refinement interactively with the DevOps team story-by-story: explain/highlight current focus, surface found issues or open questions, allow adding discussion notes as additional annotation comments (realistic daily standup scope). Invocable via slash command (e.g. `specfact.daily` or `specfact.backlog-daily`).
- **NEW**: `--summarize` flag: when set, the CLI produces a **prompt** (instructions plus applied filters and filtered standup output) suitable for use in an interactive slash-command prompt (e.g. `specfact.daily`) or copy-paste to Copilot, so an LLM can generate a meaningful **summary of the daily standup status**. Output includes filter context (adapter, state, sprint, assignee, limit) and the same per-item data as `--copilot-export`; format is prompt-ready for "generate a standup summary from this data."

## Capabilities

- **daily-standup**: Standup view (list my/filtered items with status and last activity; optional standup summary lines; default scope for state/assignee/limit; current iteration/sprint and sprint end date when supported; separate unassigned/pending items for commitment; optional blockers-first and priority/value for time-critical and value-driven focus; Kanban/Scrum/SAFe usage) and optional post standup comment to linked issue via adapter.
- **daily-standup-interactive**: Interactive selection (arrow-key, e.g. questionary) for step-by-step walkthrough of user stories in scope; per-item detail view (refine-like: description, acceptance criteria, progress, existing comments); optional next-best-item suggestion using value score (e.g. business value / (story points × priority)) when sprint goal/complexity/value/priority are available; alignment with sprint goal when defined and available.
- **daily-standup-copilot-export**: Export to file (e.g. `--copilot-export <path>`) of summarized progress per story (active/blocked/todo in current iteration/sprint) for Copilot slash-command use during standup—next steps and current progress per story for team discussion; complementary aid, not replacement for backlog.
- **backlog-project-context**: Project-level backlog config (`.specfact/backlog.yaml`) with org/project per adapter (e.g. `github.repo_owner`, `github.repo_name`; `ado.org`, `ado.project`, `ado.team`); no secrets; CLI and env override file; used by `_build_adapter_kwargs` so backlog commands can omit adapter context after one-time config.
- **daily-standup-prompt**: Slash-command prompt file `specfact.backlog-daily.md` for interactive walkthrough with DevOps team (story-by-story, current focus, issues/open questions, discussion notes as comments); usable as `specfact.daily` or `specfact.backlog-daily`.
- **daily-standup-summarize**: `--summarize` flag outputs a prompt (filters + filtered standup data) for slash command or Copilot to generate a standup summary.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #168
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/168>
- **Last Synced Status**: proposed
<!-- content_hash: 0908d647c2941d20 -->
