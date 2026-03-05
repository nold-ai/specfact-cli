## MODIFIED Requirements

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

#### Scenario: Interactive add selects from ADO constrained values

**Given**: The selected adapter is ADO and at least one mapped custom field has an allowed-values list

**When**: The user runs `specfact backlog add` in interactive mode and reaches that field prompt

**Then**: The command presents eligible values in an up/down picker

**And**: The selected option is written to the payload without requiring free-form text entry.

#### Scenario: Non-interactive add rejects invalid constrained values with hints

**Given**: The selected adapter is ADO and mapped field metadata defines allowed values

**When**: The user runs `specfact backlog add --non-interactive` with an invalid value for that field

**Then**: The command exits non-zero before create

**And**: The error message lists the allowed values for the field and suggests running interactive mode or correcting the provided value.

#### Scenario: Repeatable custom fields are parsed and mapped before create

**Given**: The user provides one or more `--custom-field key=value` options

**And**: At least one provided key maps to an ADO custom field reference via configured mapping metadata

**When**: `specfact backlog add --adapter ado` builds the create payload

**Then**: Parsed custom values are merged into provider field payload for adapter create

**And**: Unknown keys fail fast with actionable mapping guidance instead of being silently ignored.

#### Scenario: Add enforces required mapped ADO custom fields before create

**Given**: Mapped metadata marks one or more ADO custom fields as required for the selected work item type

**When**: The user omits one of those required field values

**Then**: Validation fails before adapter create call

**And**: The message identifies missing required fields and how to satisfy them.

#### Scenario: ADO create defaults text fields to markdown rendering and normalizes html-like input

**Given**: The selected adapter is ADO and the user does not pass `--description-format classic`

**When**: The command builds the provider create payload from `--body` and `--acceptance-criteria`

**Then**: The adapter sets multiline field format to `Markdown` for description and acceptance criteria by default

**And**: If provided text contains html-like content, the adapter normalizes it to markdown before submit.
