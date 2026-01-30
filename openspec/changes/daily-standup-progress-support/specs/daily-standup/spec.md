# Daily Standup

## ADDED Requirements

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
