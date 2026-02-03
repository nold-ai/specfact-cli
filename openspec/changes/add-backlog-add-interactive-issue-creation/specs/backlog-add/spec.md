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

#### Scenario: Create work item via ADO adapter

**Given**: An ADO adapter is configured and project_id is set

**When**: The user or add command calls `create_issue(project_id, payload)` with payload containing type, title, description, and optional parent_id

**Then**: The adapter maps the unified payload to ADO Create Work Item API and creates the work item

**And**: The method returns a dict with id, key, and url of the created work item

**Acceptance Criteria**:

- ADO work item type is derived from unified type via template type_mapping
- Parent link is created when parent_id is present and adapter supports it

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

**Given**: ProjectBundle.metadata.backlog_config (or .specfact/spec.yaml backlog section) contains creation_hierarchy with entries such as story: [feature, epic], task: [story]

**When**: The user adds an item with --type story --parent FEAT-1

**Then**: The system validates that "feature" is in the allowed parent types for "story" and that FEAT-1 exists and has type Feature

**And**: Validation fails clearly if parent type is not allowed

**Acceptance Criteria**:

- creation_hierarchy is optional; when absent, default or derived rules apply
- Validation uses both existence of parent in graph and allowed type from hierarchy
