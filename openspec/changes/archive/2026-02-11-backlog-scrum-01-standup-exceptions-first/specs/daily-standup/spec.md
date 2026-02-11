# Daily standup exceptions-first (E1 delta)

## ADDED Requirements

Delta on top of archived `daily-standup-progress-support`; extends `specfact backlog daily` with exceptions-first order and mode.

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
