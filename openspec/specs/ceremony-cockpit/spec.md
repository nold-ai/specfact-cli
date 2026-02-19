# ceremony-cockpit Specification

## Purpose
TBD - created by archiving change ceremony-cockpit-01-ceremony-aliases. Update Purpose after archive.
## Requirements
### Requirement: Ceremony aliases

The system SHALL provide ceremony-oriented entry points under backlog: `specfact backlog ceremony standup` (delegates to `backlog daily`), `specfact backlog ceremony refinement` (delegates to `backlog refine`), `specfact backlog ceremony planning` (delegates to `backlog sprint-summary` when installed). Optional: `backlog ceremony flow` → `backlog flow`, `backlog ceremony pi-summary` → `backlog pi-summary` when those commands exist.

**Rationale**: Δ3—findability by ceremony.

#### Scenario: Run ceremony standup

**Given**: SpecFact CLI is installed

**When**: The user runs `specfact backlog ceremony standup`

**Then**: The system executes the same behavior as `specfact backlog daily` (with same options and defaults)

**Acceptance Criteria**:

- `backlog ceremony standup` and `backlog daily` produce equivalent output for same inputs; same for refinement and planning.
- Ceremony commands inherit output formats from underlying backlog commands: human view (Markdown/table), machine view (JSON when backlog command supports `--output json`), optional copilot prompt export when supported.

#### Scenario: Missing delegated ceremony command

**Given**: A ceremony alias target command is not installed (for example `backlog sprint-summary`)

**When**: The user runs `specfact backlog ceremony planning`

**Then**: The CLI fails with a clear message describing which module command is required

**Acceptance Criteria**:

- Error message is actionable and names the missing delegate command(s).
- Failure code is non-zero.

### Requirement: Mode switch at ceremony level

The system SHALL support `--mode scrum|kanban|safe` at ceremony level so defaults for filters and sections follow the selected framework (e.g. Kanban: flow-oriented sections; SAFe: PI-oriented hints when available).

**Rationale**: Δ3—one flag for framework context.

#### Scenario: Ceremony with mode

**Given**: User runs `specfact backlog ceremony standup --mode kanban`

**When**: The command executes

**Then**: Defaults for filters and sections follow Kanban (e.g. flow/WIP context when available); output order may follow exceptions-first when data exists

**Acceptance Criteria**:

- Mode is passed through to underlying backlog command; behavior aligns with mode when backend supports it.

### Requirement: Exceptions-first default order

The system SHALL apply exceptions-first default section order (blockers, policy failures, aging, normal) for ceremony standup when Policy Engine (#176) or flow data exists; configurable or overridable.

**Rationale**: Δ3—exceptions-first by default for ceremonies.

#### Scenario: Standup with exceptions-first

**Given**: User runs `specfact backlog ceremony standup` (or `backlog daily`) and policy/flow data exists

**When**: No override disables exceptions-first

**Then**: Output sections are ordered: (1) blockers and dependency-critical, (2) policy failures, (3) aging/stalled, (4) normal status

**Acceptance Criteria**:

- Order is default when data available; existing backlog daily behavior is extended, not replaced; backward compatible.

