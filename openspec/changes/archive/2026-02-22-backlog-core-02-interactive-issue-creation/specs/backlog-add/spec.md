# Backlog Add (Interactive Issue Creation)

## ADDED Requirements

### Requirement: Backlog adapter create method

The system SHALL extend backlog adapters with a create method that accepts a unified payload and returns the created item (id, key, url).

**Rationale**: Creation is currently out-of-band (user creates in GitHub/ADO UI). CLI-driven creation with consistent payload shape allows draft → validate → create flow.

#### Scenario: Create issue via GitHub adapter

**Given**: A GitHub adapter is configured and project_id (owner/repo) is set

**When**: The user or add command calls `create_issue(project_id, payload)` with payload containing type, title, description, and optional parent_id

**Then**: The adapter maps the unified payload to GitHub Issues API (e.g. POST /repos/{owner}/{repo}/issues) and creates the issue

**And**: The method returns a dict with id, key (or number), and url of the created issue

**Acceptance Criteria**:

- Payload is provider-agnostic (type, title, description, parent_id, optional fields)
- Adapter performs provider-specific mapping (e.g. GitHub labels for type, body for description)
- Failure (auth, validation) is reported; no silent swallow
- Returned created-item identity uses canonical GitHub issue number for both `id` and `key` so follow-up parent/reference inputs resolve consistently.

#### Scenario: Create work item via ADO adapter

**Given**: An ADO adapter is configured and project_id is set

**When**: The user or add command calls `create_issue(project_id, payload)` with payload containing type, title, description, and optional parent_id

**Then**: The adapter maps the unified payload to ADO Create Work Item API and creates the work item

**And**: The method returns a dict with id, key, and url of the created work item

**Acceptance Criteria**:

- ADO work item type is derived from unified type via template type_mapping
- Parent link is created when parent_id is present and adapter supports it
- When payload includes `sprint`, adapter maps it to `System.IterationPath` in create patch payload.

### Requirement: Backlog add command

The system SHALL provide a `specfact backlog add` command that supports interactive creation of backlog issues with type selection, optional parent, title/body, validation (parent exists, allowed type, optional DoR), and create via adapter.

**Rationale**: Teams need a single flow to add well-scoped, hierarchy-aligned issues from CLI or slash prompt.

#### Scenario: Add story with parent

**Given**: A backlog graph or project is loaded (e.g. from fetch_all_issues and fetch_relationships or existing graph)

**And**: Template or backlog_config defines allowed types and creation hierarchy (e.g. Story may have parent Feature or Epic)

**When**: The user runs `specfact backlog add --type story --parent FEAT-123 --title "Implement X" --body "As a user..."` (or equivalent interactive prompts)

**Then**: The system validates that parent FEAT-123 exists in the graph and that Story is allowed under that parent type

**And**: If validation passes, the system builds a unified payload and calls the adapter's create_issue(project_id, payload)

**And**: The CLI outputs the created issue id, key, and url

**Acceptance Criteria**:

- Validation fails clearly when parent does not exist or type is not allowed
- Optional --check-dor runs DoR rules (from backlog-refinement / .specfact/dor.yaml) on the draft and warns or fails when not met

#### Scenario: Add issue with custom hierarchy

**Given**: backlog_config (or template) defines creation_hierarchy with custom allowed parent types per child type (e.g. Spike may have parent Epic or Feature)

**When**: The user runs `specfact backlog add --type spike --parent EPIC-1 --title "Spike: evaluate Y"`

**Then**: The system loads creation hierarchy from config and validates that Spike is allowed under Epic

**And**: If allowed, the system creates the issue and optionally links parent

**Acceptance Criteria**:

- Hierarchy rules are read from template or backlog_config; no hardcoded hierarchy
- Multiple levels (epic, feature, story, task, bug, spike, custom) are supported

#### Scenario: Non-interactive (scripted) add

**Given**: All required options are provided on the command line (e.g. --type, --title, --non-interactive)

**When**: The user runs `specfact backlog add --type story --title "T" --body "B" --non-interactive`

**Then**: The system does not prompt for missing fields; it uses provided values or fails with clear error for missing required fields

**And**: Validation (parent if provided, DoR if --check-dor) runs before create

**Acceptance Criteria**:

- Required fields are documented (e.g. type, title; body may be optional per provider)
- Missing required fields in non-interactive mode result in clear error exit

### Requirement: Creation hierarchy configuration

The system SHALL support configurable creation hierarchy (allowed parent types per child type) via template or backlog_config so that Scrum, SAFe, Kanban, and custom hierarchies work without code changes.

**Rationale**: Different frameworks and orgs use different trees (e.g. Story under Feature vs Story under Epic); configuration avoids hardcoding.

#### Scenario: Default hierarchy from template

**Given**: A template (e.g. ado_scrum) is selected and does not define creation_hierarchy

**When**: The add command needs to validate parent type for a new item

**Then**: The system derives allowed parent types from existing type_mapping and dependency_rules (e.g. PARENT_CHILD) where possible

**And**: If derivation is not possible, a conservative default (e.g. any type or no parent) is used and documented

#### Scenario: Custom hierarchy in backlog_config

**Given**: ProjectBundle.metadata.backlog_config (or .specfact/backlog-config.yaml) contains creation_hierarchy with entries such as story: [feature, epic], task: [story]

**When**: The user adds an item with --type story --parent FEAT-1

**Then**: The system validates that "feature" is in the allowed parent types for "story" and that FEAT-1 exists and has type Feature

**And**: Validation fails clearly if parent type is not allowed

**Acceptance Criteria**:

- creation_hierarchy is optional; when absent, default or derived rules apply
- Validation uses both existence of parent in graph and allowed type from hierarchy

### Requirement: Optional sprint assignment and linking via fuzzy match (E5)

The system SHALL support optional `--sprint <sprint-id>` so the created issue can be assigned to a sprint when the adapter and provider support it. When linking to existing issues (e.g. parent, blocks), the system SHALL support fuzzy match with user confirmation; no silent or automatic link creation.

**Rationale**: 2026-01-30 plan value chain; E5—bundle mapping and future linking.

#### Scenario: Add issue with optional sprint assignment

**Given**: Adapter and provider support sprint assignment (e.g. GitHub Projects, ADO iteration)

**When**: The user runs `specfact backlog add --type story --title "T" --sprint Sprint-1`

**Then**: The system includes sprint assignment in the payload when creating the issue (when supported)

**And**: When provider does not support sprint, the option is ignored or a clear message is shown

**Acceptance Criteria**:

- `--sprint` is optional; payload includes sprint when adapter supports it; no failure when unsupported.

#### Scenario: Link to existing issue via fuzzy match

**Given**: User specifies a parent or "blocks" target by partial key or title

**When**: The system finds one or more candidate issues (fuzzy match)

**Then**: The system presents candidates and requires user confirmation before creating the link

**And**: No link is created without explicit user confirmation

**Acceptance Criteria**:

- Fuzzy match is used for discovery only; linking requires user confirmation; no silent writes.

### Requirement: Interactive drafting fields and format selection

The system SHALL collect story-quality drafting fields during interactive creation where applicable and map them into provider payloads before create.

#### Scenario: Collect multiline body with non-conflicting sentinel

**Given**: User runs interactive `specfact backlog add` without `--body`

**When**: The command prompts for multiline body input

**Then**: The command accepts multiline text until sentinel marker is entered (default `::END::`)

**And**: The command shows immediate progress feedback that input capture is complete and creation preparation has started

#### Scenario: Collect acceptance criteria, priority, and story points for story-like types

**Given**: User selects a story-like type (story/task/feature where supported)

**When**: The command asks for quality fields

**Then**: Acceptance criteria is collected via multiline input

**And**: Priority and story points are collected (interactive prompts or explicit options)

**And**: Collected values are included in the create payload where provider supports them

#### Scenario: Select description format before create

**Given**: Interactive creation mode

**When**: The user is prompted for description format (`markdown` or `classic`)

**Then**: Selected format is included in the payload

**And**: Provider mapping respects format (for ADO: multiline field format set according to selected mode)

### Requirement: Interactive sprint/iteration and parent selection

The system SHALL prompt for sprint/iteration and parent assignment in interactive mode and validate both against provider and hierarchy constraints.

#### Scenario: Interactive sprint/iteration selection for ADO

**Given**: ADO adapter can resolve current and available iterations

**When**: User runs interactive add without `--sprint`

**Then**: The command shows selectable iteration options (including current and skip)

**And**: Selected iteration is included in payload

#### Scenario: Interactive parent selection using hierarchy constraints

**Given**: Graph and creation hierarchy are loaded

**When**: User opts to set a parent interactively

**Then**: Candidate parents are filtered to allowed parent types for selected child type

**And**: User selects parent from existing items

**And**: Selected parent id is written as `parent_id` in payload

#### Scenario: GitHub parent selection reflects mapped type consistency

**Given**: GitHub issues use label/type mapping and may include custom hierarchy labels (e.g. epic)

**When**: Parent candidates are presented

**Then**: Candidate type resolution uses current template type mapping / normalized graph type

**And**: Parent compatibility follows creation hierarchy rules with no hardcoded provider-only assumptions


### Requirement: Centralized retry policy for backlog adapter write operations

The system SHALL apply a shared retry policy for transient failures in backlog adapter create operations so command behavior is consistent across providers.

#### Scenario: Retry transient create failure and succeed

**Given**: A backlog adapter create call receives a transient failure (for example timeout, connection error, HTTP 429, or HTTP 5xx)

**When**: The command executes `create_issue`

**Then**: The adapter uses centralized retry logic with bounded attempts and backoff

**And**: If a later attempt succeeds, the command returns success with created item metadata

#### Scenario: Non-transient create failure does not retry

**Given**: A backlog adapter create call fails with non-transient error (for example HTTP 400/401/403/404)

**When**: The command executes `create_issue`

**Then**: The adapter does not retry unnecessarily

**And**: The failure is surfaced immediately to the caller with context


#### Scenario: Non-idempotent create avoids ambiguous automatic retry

**Given**: A create operation is non-idempotent and the transport fails ambiguously (for example timeout/connection drop after request may have reached provider)

**When**: The adapter executes create via shared retry core logic

**Then**: The adapter does not automatically replay the create request in that ambiguous state

**And**: The error is surfaced so caller can verify provider state and retry intentionally

### Requirement: Adapter-aware default template selection for parent hierarchy

The system SHALL default template selection by adapter when user does not explicitly pass `--template` so hierarchy/type mapping remains provider-consistent.

#### Scenario: ADO backlog add defaults to ado_scrum mapping

**Given**: User runs `specfact backlog add --adapter ado` without `--template`

**When**: The command builds graph and parent candidates

**Then**: It uses ADO-compatible template mapping (default `ado_scrum`)

**And**: Epic/feature/story hierarchy candidates are resolved consistently for parent selection


### Requirement: Shared retry policy applied consistently across adapter write operations

The system SHALL apply centralized retry policy to backlog adapter write operations beyond create, with operation-specific ambiguity safety.

#### Scenario: Non-idempotent write uses duplicate-safe mode

**Given**: Adapter operation is non-idempotent (for example comment creation)

**When**: Shared retry helper is used

**Then**: Ambiguous transport replay is disabled to avoid duplicate side effects

#### Scenario: Idempotent update uses bounded transient retry

**Given**: Adapter operation is idempotent (for example status/body patch)

**When**: Shared retry helper is used

**Then**: Transient HTTP failures are retried with bounded backoff

**And**: Non-transient failures are surfaced immediately


### Requirement: Parent candidate discovery must not exclude valid hierarchy parents by implicit sprint defaults

The system SHALL avoid implicit current-iteration filtering when loading parent candidates for interactive parent selection.

#### Scenario: ADO parent candidate fetch includes epics without sprint assignment

**Given**: User creates a feature and opts to choose parent interactively in ADO

**When**: Parent candidates are loaded for hierarchy filtering

**Then**: Parent discovery does not implicitly limit candidates to current iteration

**And**: Epics/features outside current iteration remain selectable when hierarchy allows

### Requirement: User warning on duplicate-safe ambiguous create failure

The system SHALL display a user-facing warning when non-idempotent create fails due to ambiguous transport errors while duplicate-safe retry mode is active.

#### Scenario: Timeout/connection drop on duplicate-safe create

**Given**: Create uses duplicate-safe mode (no ambiguous replay)

**When**: Create fails with timeout/connection error

**Then**: CLI warns the user that the item may have been created remotely

**And**: CLI advises verifying backlog before retrying manually


#### Scenario: ADO sprint selection resolves iterations using project_id context

**Given**: User runs `backlog add` with `--adapter ado --project-id <org>/<project>` and adapter defaults do not already include org/project

**When**: Interactive sprint/iteration selection is shown

**Then**: The command resolves ADO org/project context from project_id for iteration API calls

**And**: Available iterations are listed for selection when accessible


#### Scenario: GitHub backlog add forwards Projects Type field configuration

**Given**: `backlog add` runs with GitHub adapter and template/custom config contains GitHub Projects v2 type field mapping metadata

**When**: The command builds create payload for `create_issue`

**Then**: It forwards provider field metadata in payload (for example `provider_fields.github_project_v2`) so the adapter can set the Projects `Type` field in addition to labels


#### Scenario: GitHub ProjectV2 Type mapping can come from repo backlog provider settings

**Given**: `.specfact/backlog-config.yaml` defines `backlog_config.providers.github.settings.provider_fields.github_project_v2`

**When**: `backlog add` runs with GitHub adapter and no explicit `--custom-config`

**Then**: The command forwards that provider field configuration in create payload so adapter ProjectV2 Type mapping can run


#### Scenario: GitHub add warns when ProjectV2 Type mapping config is absent

**Given**: User runs `backlog add` with GitHub adapter and no ProjectV2 Type mapping metadata is available

**When**: The command prepares create payload

**Then**: The command prints a warning that GitHub ProjectV2 Type field will not be set automatically and labels/body fallback is used


#### Scenario: GitHub custom mapping file auto-applies when present

**Given**: `--adapter github` and no `--custom-config` flag is provided
**And**: `.specfact/templates/backlog/field_mappings/github_custom.yaml` exists
**When**: The user runs `specfact backlog add`
**Then**: The command loads `github_custom.yaml` as custom mapping/hierarchy overrides
**And**: Parent validation and candidate filtering use those overrides
**And**: If the file does not exist, the command falls back to default `github_projects` mapping behavior.


#### Scenario: GitHub parent is linked using native sub-issue relationship

**Given**: A GitHub parent issue is selected during `backlog add`
**When**: The issue is created
**Then**: The adapter links parent/child using GitHub native issue relationship (`addSubIssue`) so the right-sidebar parent relation is populated
**And**: Body text markers are secondary compatibility metadata, not the primary relationship mechanism.
