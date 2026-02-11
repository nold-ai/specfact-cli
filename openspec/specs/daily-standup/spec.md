# daily-standup Specification

## Purpose
TBD - created by archiving change daily-standup-progress-support. Update Purpose after archive.
## Requirements
### Requirement: Standup view

The system SHALL provide a standup or progress view that lists change proposals or backlog items (by assignee or filter) with last-updated and status, and optional one-line summary for yesterday/today/blockers.

**Rationale**: Teams need a single place to see "my items" and recent activity for daily standup without duplicating data in multiple tools.

#### Scenario: List my items with status and last activity

**Given**: A user has change proposals or backlog items assigned to them (or a filter is applied)

**When**: The user runs the standup view (e.g. `specfact backlog daily` or equivalent under the backlog command group)

**Then**: The system lists items (change proposal id or backlog item id, title, status, last-updated) for the user or filter

**And**: Optional standup summary lines (yesterday/today/blockers) are shown when available from proposal or linked issue body

**Acceptance Criteria**:

- Output is readable (e.g. table or structured list)
- Last-updated is displayed per item
- Optional standup fields (yesterday, today, blockers) shown when present in source data

#### Scenario: Standup view with assignee filter

**Given**: A repo with multiple change proposals or backlog items and assignee metadata

**When**: The user runs standup view with assignee filter (e.g. `--assignee me` or current user)

**Then**: Only items matching the assignee are listed

**And**: If no assignee filter is applied, all items (or default scope) are listed per command contract

### Requirement: Default standup scope (meaningful daily standups)

The system SHALL support a default standup scope so daily standups focus on active work, not the full backlog: default state filter (e.g. open/active), optional default assignee (e.g. current user when resolvable), and default limit (e.g. 20–30 items). Defaults SHALL be overridable by explicit options and SHALL be configurable via environment variables and/or a config file (e.g. `.specfact/standup.yaml`).

**Rationale**: Without defaults, `specfact backlog daily` can list the entire backlog; standups should default to "active items and recent activity" so the view is immediately useful.

#### Scenario: Standup view uses default scope when no filters given

**Given**: Standup defaults are configured (e.g. state=open, limit=20) or built-in (state=open, limit=20)

**When**: The user runs standup view without explicit `--state`, `--assignee`, or `--limit`

**Then**: The system applies the default state filter (e.g. open) so closed/done items are excluded

**And**: The system applies the default limit (e.g. 20) so output is scannable

**And**: If configured, default assignee (e.g. "me") is applied so "my items" are shown by default

**Acceptance Criteria**:

- Explicit `--state`, `--assignee`, `--limit` override defaults
- Config (env or file) takes precedence over built-in defaults when present
- When adapter has no "open" equivalent, state default is documented (e.g. skip or use adapter's active state)

### Requirement: Current iteration/sprint focus

The system SHALL support focusing the standup view on the current iteration or sprint when the adapter provides iteration/sprint metadata (e.g. GitHub Projects, ADO iteration). A parameter (e.g. `--sprint current` or `--iteration current`) or config SHALL filter items to the current iteration/sprint so "new items to start" in the sprint are visible and can be committed to during standup.

**Rationale**: Daily standups need to see both "what I'm working on" and "what's in the sprint but not yet assigned" so the team can commit to new work.

#### Scenario: Standup view filtered to current iteration/sprint

**Given**: An adapter that supports iteration or sprint (e.g. ADO with iteration path, or GitHub with project/sprint)

**When**: The user runs standup view with current iteration/sprint (e.g. `--sprint current` or config `sprint: current`)

**Then**: The system lists only items in the current iteration/sprint (or current active sprint when adapter supports it)

**And**: If the adapter does not support iteration/sprint, the option is ignored or reported clearly; no crash

**Acceptance Criteria**:

- When supported, "current" resolves to the adapter's notion of current sprint/iteration
- When current iteration/sprint is in use and the adapter or config provides an iteration/sprint end date, the standup view displays it (e.g. "Sprint ends: DATE (N days)")
- Documentation states which adapters support iteration/sprint filtering

### Requirement: Unassigned/pending items view

The system SHALL show items with no assignee (backfill, open sprint, or pending) so the team can discuss and commit to picking them up during standup. Unassigned items SHALL be available either in a separate table (e.g. "Pending / open for commitment") or via an additional parameter (e.g. `--unassigned` / `--pending`) that includes or exclusively shows unassigned items in the same scope (e.g. same state and iteration).

**Rationale**: Standups are not only about "what I did / what I'll do" but also "new items in the iteration that need commitment from the team"; unassigned items must be visible and discussable.

#### Scenario: Unassigned items shown for standup commitment

**Given**: A backlog with items in the current scope (e.g. open, current sprint) some of which are assigned and some unassigned

**When**: The user runs standup view with unassigned items enabled (e.g. default, or `--unassigned`, or `--show-pending`)

**Then**: The system shows assigned items (e.g. in a "My / assigned" table or section) and unassigned items (e.g. in a separate "Pending / open for commitment" table or section) so both can be discussed

**And**: Unassigned items use the same scope (state, iteration/sprint if applied) so they are relevant to the current iteration

**Acceptance Criteria**:

- Unassigned items are clearly labeled (e.g. separate table title or column)
- Option to show only unassigned (e.g. `--unassigned-only`) is available for teams that want to run "pick up" separately
- When no unassigned items exist in scope, the unassigned section is omitted or shows "None"

### Requirement: Blockers and time-critical prominence

The system SHALL support optionally sorting or surfacing items with non-empty blockers so time-critical issues are visible at a glance (e.g. sort rows with blockers first, or a `--blockers-first` flag).

**Rationale**: Daily standups need to surface blockers early so the team can address time-critical issues during the current iteration.

#### Scenario: Standup view with blockers first

**Given**: Backlog items in the standup view, some with non-empty standup blockers text

**When**: The user runs standup view with blockers-first enabled (e.g. `--blockers-first` or default sort)

**Then**: Items with non-empty blockers are listed first (or in a dedicated order) so blockers are easy to spot

**Acceptance Criteria**:

- When supported, items with non-empty blockers may be listed first (e.g. sort or `--blockers-first`), so blockers are easy to spot

### Requirement: Optional priority/value in standup view

The system SHALL support optionally showing priority or business value in the standup view when available on BacklogItem and enabled by config, so value-driven (e.g. SAFe) teams can focus on the right features.

**Rationale**: Value-driven prioritization (WSJF, priority) helps teams deliver the right features during the iteration.

#### Scenario: Standup view shows priority or value when enabled

**Given**: Backlog items have priority or business_value (or value_points) and standup config enables showing priority/value

**When**: The user runs standup view with priority/value display enabled (e.g. config or option)

**Then**: The standup table includes a priority or value column (or equivalent) when the data is present on items

**Acceptance Criteria**:

- When priority or business value is available on BacklogItem and enabled by config, the standup view may display it (e.g. optional column)

### Requirement: Post standup comment to linked issue

The system SHALL support posting a standup summary as a comment on the linked issue (e.g. GitHub issue comment) when the user opts in and the adapter supports it.

**Rationale**: Standup updates should be visible in the DevOps backend (GitHub, ADO) so the team sees progress where they work.

#### Scenario: Post standup comment via GitHub adapter

**Given**: A change proposal with Source Tracking linking to a GitHub issue (e.g. nold-ai/specfact-cli#N)

**And**: The user has provided standup text (yesterday/today/blockers format) and opts to post (e.g. `specfact backlog daily --post` or equivalent)

**When**: The user runs `specfact backlog daily --post` (or equivalent) and GitHub adapter is configured

**Then**: The system adds a comment to the linked GitHub issue with the standup text (format: Yesterday / Today / Blockers or team-defined format)

**And**: The comment is clearly identifiable (e.g. "Standup YYYY-MM-DD" or configurable prefix)

**Acceptance Criteria**:

- Comment is posted only when user opts in and adapter supports comments
- Format is configurable or follows a simple standard (yesterday, today, blockers)
- Failure to post (e.g. auth, rate limit) is reported clearly; no silent swallow

#### Scenario: Post standup when adapter does not support comments

**Given**: An adapter that does not support posting comments (e.g. read-only or no comment API)

**When**: The user runs `specfact backlog daily --post` (or equivalent)

**Then**: The system reports that posting is not supported for this adapter and does not attempt to post

**Acceptance Criteria**:

- Clear message; no crash or undefined behavior

### Requirement: Interactive step-by-step review

The system SHALL support an interactive step-by-step review of backlog items in the same scope as the standup view (state, iteration/sprint, assignee, limit, unassigned), using arrow-key selection (e.g. questionary) so the user can walk through each story and see full details including progress and existing comments. The feature is complementary to the backlog; it does not replace the backlog or board.

**Rationale**: Teams need to review each story in detail during standup (blocked items, which to pick next) with minimal context switching; interactive selection and refine-like detail support informed feedback and decision-making.

#### Scenario: Interactive selection presents items and shows detail on choice

**Given**: Backlog items in the current scope (e.g. current iteration/sprint, active/blocked/todo) and the user runs `specfact backlog daily --interactive` (or equivalent)

**When**: The interactive mode starts

**Then**: The system presents a list of choices (one per backlog item), selectable by arrow keys (e.g. questionary), with each choice showing a summary line (e.g. id, title, status, assignee)

**And**: When the user selects an item, the system displays full details comparable to `specfact backlog refine` for that item: ID, title, status, assignees, last updated, description/body, acceptance criteria, story points, business value, priority when available, standup fields (yesterday/today/blockers), and **existing comments annotated to that issue** (fetched via adapter when supported, e.g. GitHub issue comments, ADO work item discussion)

**And**: Items with non-empty blockers are clearly indicated (e.g. blocked status highlighted)

**Acceptance Criteria**:

- Selection UI is consistent with existing questionary usage (e.g. template field mapping)
- Detail view reuses or aligns with refine output (description, acceptance criteria, **comments**)
- **Comments**: The system SHALL show comments annotated to the selected issue when the adapter supports fetching comments (e.g. get_comments); omitted or empty when adapter does not support or returns none

#### Scenario: Interactive navigation (next / previous / back / exit)

**Given**: User is in interactive mode and has just viewed detail for one item

**When**: The system presents navigation choices (e.g. "Next story", "Previous story", "Back to list", "Exit")

**Then**: "Next story" shows detail for the next item in the current ordered list without re-opening the full item menu

**And**: "Previous story" shows detail for the previous item

**And**: "Back to list" returns to the item selector menu

**And**: "Exit" ends the command

**Acceptance Criteria**:

- Next/Previous wrap or stop at list boundaries (documented behavior)
- No re-fetch of list when moving next/previous; use already-fetched items

#### Scenario: Optional next-best-item suggestion and sprint goal hint

**Given**: BacklogItem or adapter provides story_points, business_value, and priority for some items; optionally sprint goal is provided by adapter or config

**When**: Interactive mode is run with suggestion enabled (e.g. config or `--suggest-next`)

**Then**: The system may show a "Suggested next: <id> - <title>" (or value score) for pending (e.g. todo/unassigned) items using a value score (e.g. business_value / max(1, story_points * priority)) so higher value per effort is suggested

**And**: When sprint goal is available (adapter or config), the interactive view may display an optional hint (e.g. "Sprint goal: …") so the user can align; sprint goal is not edited by the system

**Acceptance Criteria**:

- Value score is omitted when required fields are missing; no fake values
- Suggestion is optional (config or flag); default can be off to avoid noise
- Sprint goal hint is optional and read-only

### Requirement: Export to file for Copilot

The system SHALL support exporting a summarized view of each backlog item in the current standup scope (current iteration/sprint, active/blocked/todo) to a file, formatted for use with Copilot slash-command interactive review during standup (e.g. summarize progress and next steps per story for team discussion). The export is complementary to the backlog; it does not replace the backlog or board.

**Rationale**: Teams using Copilot during standup need a concise, file-based summary of each story so Copilot can assist with next steps and current progress; the file is for paste or reference in slash commands.

#### Scenario: Copilot export writes summarized items to file

**Given**: Backlog items in the current scope (same as standup: state, iteration/sprint, assignee, limit) and the user runs `specfact backlog daily --copilot-export <path>` (or equivalent)

**When**: The command runs (with or without `--interactive`; export uses the same fetched list)

**Then**: The system writes a file at the given path with one section per backlog item in scope

**And**: Each section includes at least: ID, title, status, assignee(s), last updated, short progress summary (standup fields if present), blockers; optionally value score, priority, story points when available

**And**: Format is Markdown with clear headings (e.g. `## <id> - <title>`) and bullet points for quick scanning and Copilot use

**Acceptance Criteria**:

- File is overwritten (idempotent write) or behavior is configurable
- Export builder has @icontract and @beartype where applicable
- When both `--interactive` and `--copilot-export` are given, export runs on the same fetched list (no requirement to re-fetch)

### Requirement: Slash-command prompt for daily standup (specfact.backlog-daily)

The system SHALL provide a prompt file (e.g. `resources/prompts/specfact.backlog-daily.md`) analogous to `specfact.backlog-refine.md`, so teams can run the daily standup flow interactively with the DevOps team via a slash command (e.g. `specfact.daily` or `specfact.backlog-daily`). The prompt SHALL instruct the AI to walk through stories story-by-story, explain and highlight current focus, surface found issues or open questions, and allow adding discussion notes as additional annotation comments on the issue (realistic daily standup scope).

**Rationale**: Teams need a single, reusable prompt for IDE/Copilot that drives a structured standup review (refinement-style walkthrough with option to add discussion notes as comments), without duplicating instructions in each session.

#### Scenario: Slash command invokes daily standup prompt

**Given**: The user invokes the slash command (e.g. `/specfact.daily` or `/specfact.backlog-daily`) with optional adapter and filter arguments

**When**: The prompt file is loaded and combined with the current context (e.g. CLI output or `--summarize` output)

**Then**: The AI follows the prompt to present items story-by-story, highlight focus, issues, and open questions, and may suggest or add discussion notes as comments when the user approves

**Acceptance Criteria**:

- Prompt file exists under `resources/prompts/` and is documented (e.g. in tutorial and devops-adapter-integration)
- Prompt content aligns with interactive daily flow: story-by-story review, current focus, issues/open questions, discussion notes as comments
- Prompt can be used with `specfact backlog daily` output (e.g. `--copilot-export` or `--summarize`) as input context

### Requirement: Standup summary prompt (--summarize)

The system SHALL support a `--summarize` flag on `specfact backlog daily` that produces a **prompt** (instructions plus applied filters and filtered standup output) suitable for use in an interactive slash command (e.g. `specfact.daily`) or copy-paste to Copilot, so an LLM can generate a meaningful **summary of the daily standup status**.

**Rationale**: Teams want one command that dumps the current standup view into a prompt-ready format, so Copilot or a slash command can then produce a short narrative summary (e.g. "Today's standup: 3 in progress, 1 blocked, 2 pending commitment …") without manually re-typing filters or data.

#### Scenario: --summarize outputs prompt with filters and data

**Given**: Backlog items in the current scope (same as standup: state, iteration/sprint, assignee, limit) and the user runs `specfact backlog daily --summarize` (stdout) or `--summarize-to <path>` (write to file)

**When**: The command runs with the same filters as the standup view

**Then**: The system outputs (to stdout or to the given path) a prompt that includes: (1) brief instruction that the following data is the current standup view and the LLM should generate a concise standup summary; (2) the applied filter context (adapter, state, sprint, assignee, limit); (3) per-item data including **body (description)** and **comments (annotations)** when available, plus ID, title, status, assignees, last updated, progress, blockers, optional value score, so the LLM can produce a **meaningful** summary

**And**: The output is formatted so it can be pasted into Copilot or used as input to a slash command (e.g. `specfact.daily`) to produce a standup summary

**Acceptance Criteria**:

- `--summarize` uses the same fetched list and filters as the standup view (and as `--copilot-export`)
- Output includes filter context and per-item data; **per-item data SHALL include body (description)** and **comments (annotations)** when the adapter supports fetching comments, so the LLM can create a meaningful summary
- Format is prompt-ready (e.g. Markdown with clear "Generate a standup summary from the following" instruction)
- When `--summarize` or `--summarize-to` is used, the command outputs **only** the prompt (no standup tables) and then exits
- When `--summarize-to <path>` is given, write to file; when `--summarize` only is given, output to stdout
- When both `--summarize` and `--copilot-export` are given, both outputs can be produced from the same fetched list

### Requirement: Project backlog context (no secrets)

The system SHALL support storing project-level backlog context (org, project per adapter) in the repo so users do not have to pass adapter context (e.g. `--repo-owner`, `--repo-name`, `--ado-org`, `--ado-project`) every time after authenticating once. Context SHALL be stored in `.specfact/backlog.yaml` (or equivalent) and SHALL contain only non-sensitive identifiers (no tokens, no user names). Resolution order SHALL be: explicit CLI args > environment variables (e.g. `SPECFACT_GITHUB_REPO_OWNER`) > file. Tokens SHALL never be read from file.

**Rationale**: After one-time authentication (tokens in env or keychain), teams want to set org/project once per repo so all backlog commands (daily, refine, sync bridge) work without repeating adapter options.

#### Scenario: Adapter context from project config when not passed

**Given**: A repo with `.specfact/backlog.yaml` containing e.g. `github.repo_owner`, `github.repo_name` (or `ado.org`, `ado.project`, `ado.team`)

**When**: The user runs a backlog command (e.g. `specfact backlog daily github`) without passing `--repo-owner` or `--repo-name`

**Then**: The system uses repo_owner and repo_name from the project config (or env) so the command succeeds without explicit options

**And**: Explicit CLI options override config and env

**Acceptance Criteria**:

- File format supports per-adapter keys (e.g. `github.repo_owner`, `github.repo_name`; `ado.org`, `ado.project`, `ado.team`)
- Env overrides file (e.g. `SPECFACT_GITHUB_REPO_OWNER`, `SPECFACT_ADO_ORG`)
- Tokens are never read from file; only from CLI or env
- Config is loaded from `SPECFACT_CONFIG_DIR` or `.specfact/` in cwd; first found wins
- When org/repo or org/project are still missing after CLI, env, and file, the system MAY infer from `git remote get-url origin` when run from a clone (GitHub or Azure DevOps URL formats); supported ADO formats: HTTPS, SSH with keys (`git@ssh.dev.azure.com:v3/...`), SSH without keys (`user@dev.azure.com:v3/...`). If inference fails or not in a clone, the system SHALL report a clear error with guidance (CLI, env, or `.specfact/backlog.yaml`).

### Requirement: Exceptions-first section order

The system SHALL order `specfact backlog daily` output sections by default as: (1) blockers and dependency-critical items, (2) policy failures (DoR/DoD/flow when Policy Engine available), (3) aging items / stalled work (when data exists), (4) normal status.

**Rationale**: Plan E1—teams see risks first.

#### Scenario: Standup output shows exceptions first

**Given**: Policy Engine (unify-policies-engine) and/or aging/flow data are available

**When**: The user runs `specfact backlog daily` (no override)

**Then**: The output includes an "Exceptions" section by default (blockers, policy failures, aging/stalled when available) before normal status

**Acceptance Criteria**:

- `backlog daily` includes an "Exceptions" section by default when exception data exists.

### Requirement: Mode switch (scrum|kanban|safe)

The system SHALL support `--mode scrum|kanban|safe` to change defaults for filters and sections (e.g. Kanban: flow columns; SAFe: PI context).

**Rationale**: Plan E1—ceremony-native defaults per framework.

#### Scenario: Standup with mode

**Given**: SpecFact CLI and backlog adapter

**When**: The user runs `specfact backlog daily --mode kanban`

**Then**: Default filters and section behavior align with Kanban (e.g. flow-focused); when `--mode safe`, PI context when available

**Acceptance Criteria**:

- `--mode scrum|kanban|safe` changes defaults; existing backlog daily behavior otherwise unchanged.

### Requirement: Patch integration for standup notes

The system SHALL integrate with patch mode (patch-mode-preview-apply) to propose standup notes or missing fields as patch when `--patch` is used.

**Rationale**: Plan E1—actionable standup output.

#### Scenario: Standup with patch proposal

**Given**: Patch mode is available

**When**: The user runs `specfact backlog daily --patch`

**Then**: The command may emit a patch proposal (standup notes or missing fields) for user review/apply

**Acceptance Criteria**:

- When patch mode is available and `--patch` is set, standup can propose patch; no silent writes.

### Requirement: Interactive standup comment display is scoped

The system SHALL avoid dumping full comment history in interactive standup detail views. When comments exist, it SHALL show only the latest comment by default and provide a clear hint that full comments are available via export options.

**Rationale**: Interactive review must stay readable while still giving users access to complete context in export workflows.

#### Scenario: Interactive view shows latest comment and export hint

**Given**: The selected backlog item has multiple comments (e.g., from ADO work item discussion)

**When**: The user runs `specfact backlog daily --interactive` and opens the item detail view

**Then**: The detail view shows only the latest comment text

**And**: The detail view shows how many additional older comments exist

**And**: The detail view includes a hint to use export-to-file options to retrieve all comments

**Acceptance Criteria**:

- Interactive detail output does not render all comments inline when more than one exists.
- The output explicitly guides users to export for full comment context.

#### Scenario: Interactive comment-window override is honored

**Given**: The user runs `specfact backlog daily --interactive --first-comments N` or `--last-comments N`

**When**: The selected backlog item has more comments than N

**Then**: The interactive detail view renders the selected window of N comments (instead of latest-only default)

**And**: The detail view clearly indicates how many additional comments were omitted by the window

#### Scenario: Interactive comments use scoped panel-style blocks

**Given**: The user runs `specfact backlog daily --interactive`

**When**: Comment context is rendered for a selected item

**Then**: Comments are rendered in clear scoped blocks (panel-style), separate from the story detail body, for readability

### Requirement: Comment window controls for standup exports and summarize prompts

The system SHALL support optional comment-window controls `--first-comments N` and `--last-comments N` for `specfact backlog daily` exports/prompts that include comments. By default, no comment truncation is applied.

**Rationale**: Teams need complete context by default, but must be able to constrain prompt size when needed.

#### Scenario: Export/summarize uses all comments by default

**Given**: The user runs `specfact backlog daily --comments` with `--copilot-export`, `--summarize`, or `--summarize-to`

**When**: No `--first-comments` or `--last-comments` option is provided

**Then**: The command includes all available comments per item (no truncation)

#### Scenario: First-comments limit is applied

**Given**: The user runs `specfact backlog daily --comments --first-comments 3 --copilot-export <path>`

**When**: An item has more than three comments

**Then**: The output includes only the first three comments for that item

#### Scenario: Last-comments limit is applied

**Given**: The user runs `specfact backlog daily --comments --last-comments 2 --summarize`

**When**: An item has more than two comments

**Then**: The output includes only the last two comments for that item

**Acceptance Criteria**:

- Default behavior is full comment inclusion.
- First/last limits are optional and deterministic.
- If both are provided, command fails with a clear validation error.

### Requirement: Assignee visibility and GitHub `me` filter semantics

The system SHALL show assignment context directly in `specfact backlog daily` table output and SHALL handle GitHub assignee filter value `me` (or `@me`) as provider-relative current-user semantics rather than a literal username string.

**Rationale**: Daily standup output must make ownership explicit, and GitHub users commonly use `me` as shorthand in issue filtering.

#### Scenario: Daily table includes assignee column

**Given**: The user runs `specfact backlog daily` and at least one item has assignees

**When**: The standup table is rendered

**Then**: The table includes an `Assignee` column

**And**: Each row shows comma-separated assignees or `—` when unassigned

#### Scenario: GitHub `--assignee me` uses provider semantics

**Given**: The adapter is GitHub and the user passes `--assignee me` (or `--assignee @me`)

**When**: The command fetches and post-filters backlog items

**Then**: The GitHub query uses provider-relative current-user qualifier semantics

**And**: Local post-fetch filtering does not treat `me` as a literal assignee login

**Acceptance Criteria**:

- `backlog daily` output includes an assignee column.
- GitHub `me`/`@me` filtering is deterministic and does not get incorrectly narrowed by literal local matching.

### Requirement: Issue window controls for backlog daily

The system SHALL support optional issue-window controls `--first-issues N` and `--last-issues N` on `specfact backlog daily` with deterministic numeric issue ID ordering semantics matching `specfact backlog refine`.

**Rationale**: Users need harmonized backlog command ergonomics to focus on oldest/newest slices without changing workflows between subcommands.

#### Scenario: Daily command supports first-issues window

**Given**: More than N items match `specfact backlog daily` filters

**When**: The user runs `specfact backlog daily ... --first-issues N`

**Then**: Only the lowest N numeric issue/work-item IDs are included in output

#### Scenario: Daily command supports last-issues window

**Given**: More than N items match `specfact backlog daily` filters

**When**: The user runs `specfact backlog daily ... --last-issues N`

**Then**: Only the highest N numeric issue/work-item IDs are included in output

#### Scenario: Daily command rejects conflicting issue windows

**Given**: The user passes both `--first-issues` and `--last-issues`

**When**: The command validates CLI inputs

**Then**: The command exits with a clear validation error

**Acceptance Criteria**:

- `backlog daily` has `--first-issues` and `--last-issues` options.
- Only one issue window option can be used at once.
- Ordering semantics align with refine (`first`=lowest numeric IDs, `last`=highest numeric IDs).
- Issue windowing is applied over the full filtered candidate set (not a pre-truncated default-limit subset).

### Requirement: Global filter parity across backlog commands

The system SHALL provide consistent global backlog filtering flags across `specfact backlog daily` and `specfact backlog refine` for shared backlog-item selection semantics.

#### Scenario: Daily supports shared global filter flags

**Given**: The user runs `specfact backlog daily`

**When**: They use global filters available on refine

**Then**: Daily accepts and applies `--search`, `--release`, and `--id` consistently with refine semantics

**Acceptance Criteria**:

- `backlog daily` accepts `--search`, `--release`, and `--id`.
- `--search` and `--release` are applied in fetch/filter flow.
- `--id` narrows to the exact backlog item ID after other filters; when not found, command exits with a clear error.

### Requirement: Interactive standup can post comment for selected issue

The system SHALL allow posting standup comments directly from the interactive review flow for the currently selected item.

**Rationale**: Teams review one story at a time during daily standup; posting from the selected item avoids context switching and reduces mistakes.

#### Scenario: Post standup comment from selected story in interactive mode

**Given**: The user runs `specfact backlog daily --interactive`

**And**: The adapter supports `add_comment`

**When**: The user opens a story and chooses the interactive post action

**Then**: The CLI prompts for standup fields (yesterday/today/blockers)

**And**: The CLI posts the comment to that selected story (not implicitly to another item)

**And**: The CLI shows a clear success or failure message

**Acceptance Criteria**:

- Interactive navigation includes a post action for the selected story.
- Empty post input is rejected with a clear message.
- Posting uses existing standup comment format and adapter capability checks.

