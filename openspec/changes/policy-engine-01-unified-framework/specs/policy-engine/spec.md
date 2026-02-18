# Policy Engine (DoR/DoD/Flow/PI)

## ADDED Requirements

### Requirement: Policy validate (deterministic, hard failures)

The system SHALL provide `specfact policy validate` that runs policy rules deterministically and reports hard failures (rule id, severity, evidence pointer, recommended action). It SHALL run without network access when using snapshots.

**Rationale**: Plan Δ1—consistent quality gates.

#### Scenario: Validate policies

**Given**: A project with `.specfact/policy.yaml` and backlog/spec snapshot

**When**: The user runs `specfact policy validate`

**Then**: The system evaluates all configured policies and outputs failures (rule id, severity, evidence pointer, recommended action)

**And**: Output is machine-readable (JSON) and human-readable (Markdown)

**Acceptance Criteria**:

- Policy results include: rule id, severity, evidence pointer (field/path), recommended action; no network required when using snapshots.

### Requirement: Policy input auto-discovery from .specfact artifacts

The system SHALL automatically resolve policy input artifacts from existing `.specfact` backlog outputs when `--snapshot` is omitted.

**Rationale**: Align policy validation with existing foundation schemas and artifact locations.

#### Scenario: Use backlog baseline automatically

**Given**: `.specfact/policy.yaml` exists

**And**: `.specfact/backlog-baseline.json` exists

**When**: The user runs `specfact policy validate` without `--snapshot`

**Then**: The system loads policy-evaluable items from `.specfact/backlog-baseline.json`

**And**: Policy validation executes without requiring manual snapshot path input.

#### Scenario: Fallback to latest backlog plan artifact

**Given**: `.specfact/policy.yaml` exists

**And**: `.specfact/backlog-baseline.json` does not exist

**And**: `.specfact/plans/backlog-*.yaml` or `.specfact/plans/backlog-*.json` exists

**When**: The user runs `specfact policy validate` without `--snapshot`

**Then**: The system selects the latest backlog plan artifact

**And**: Extracts policy-evaluable items from its `backlog_graph` structure.

### Requirement: Policy input format normalization

The system SHALL normalize known backlog artifact payload formats into policy-evaluable item arrays.

**Rationale**: Existing foundation modules serialize backlog data with multiple compatible shapes.

#### Scenario: Normalize graph-shaped payload with dict items

**Given**: Policy input payload includes `items` as an object keyed by item id

**When**: The user runs `specfact policy validate`

**Then**: The loader converts `items` values to an array of item objects before rule evaluation.

#### Scenario: Normalize plan payload with backlog_graph wrapper

**Given**: Policy input payload includes `backlog_graph.items`

**When**: The user runs `specfact policy validate`

**Then**: The loader extracts and normalizes `backlog_graph.items` for evaluation.

### Requirement: Policy field compatibility mapping for imported backlog artifacts

The system SHALL map common provider and backlog-graph fields into policy field names so policy checks operate on imported artifacts without requiring manual data reshaping.

**Rationale**: Imported foundation artifacts store rich metadata in provider-shaped fields and `raw_data`.

#### Scenario: Resolve required fields from raw_data aliases

**Given**: An item lacks top-level `acceptance_criteria`, `business_value`, or `definition_of_done`

**And**: Equivalent values exist in `raw_data` (for example provider keys like `System.AcceptanceCriteria`, `Microsoft.VSTS.Common.BusinessValue`, or normalized aliases)

**When**: The user runs `specfact policy validate`

**Then**: The policy input normalizer resolves those aliases into standard policy field names before rule evaluation.

#### Scenario: Resolve acceptance criteria and DoD from description sections

**Given**: An item description contains sections for acceptance criteria and definition of done

**When**: The user runs `specfact policy validate`

**Then**: The normalizer extracts those sections as `acceptance_criteria` and `definition_of_done` for policy evaluation.

### Requirement: Policy suggest (AI-assisted, patch-ready)

The system SHALL provide `specfact policy suggest` that proposes fixes with confidence scores and patch-ready output when applicable; user confirmation required before apply.

**Rationale**: Plan Δ1—actionable suggestions without silent writes.

#### Scenario: Suggest policy fixes

**Given**: Policy validate has reported failures

**When**: The user runs `specfact policy suggest`

**Then**: The system proposes fixes (e.g. missing fields, DoR gaps) with confidence and optional patch; no write without explicit user action

**Acceptance Criteria**:

- Suggestions are confidence-scored and patch-ready; no automatic writes.

### Requirement: Policy output filtering and limiting

The system SHALL support filtering and limiting policy findings/suggestions so large result sets remain actionable.

**Rationale**: Real backlog snapshots can produce hundreds of findings.

#### Scenario: Filter by rule id

**Given**: Policy evaluation produced findings across multiple rule ids

**When**: The user runs `specfact policy validate --rule scrum.dor.acceptance_criteria`

**Then**: Only findings matching the requested rule filter are displayed and returned.

#### Scenario: Limit output size

**Given**: Policy evaluation produced many findings

**When**: The user runs `specfact policy suggest --limit 10`

**Then**: At most ten suggestions are returned in command output.

#### Scenario: Grouped output limit applies to item groups

**Given**: Policy evaluation produced findings for multiple backlog items

**When**: The user runs `specfact policy validate --group-by-item --limit 4`

**Then**: At most four backlog item groups are returned

**And**: Each returned group includes all findings/suggestions for that item after rule filtering.

### Requirement: Policy grouped output by item

The system SHALL provide optional grouped output by backlog item for validate/suggest commands.

**Rationale**: Item-centric remediation is easier than scanning flat finding lists.

#### Scenario: Group validate output by item

**Given**: Policy evaluation produced failures for multiple `items[N]` evidence pointers

**When**: The user runs `specfact policy validate --group-by-item`

**Then**: Output includes grouped sections keyed by item index.

#### Scenario: Group suggest output by item

**Given**: Policy suggestions were generated for multiple items

**When**: The user runs `specfact policy suggest --group-by-item`

**Then**: Output includes per-item suggestion groups and summary metadata only (no duplicate top-level flat suggestion list).

### Requirement: Policy config

The system SHALL support policy configuration in `.specfact/policy.yaml` (Scrum: DoR/DoD; Kanban: entry/exit per column; SAFe: PI readiness hooks).

**Rationale**: Plan Δ1—one config, one engine.

#### Scenario: Load policy config

**Given**: `.specfact/policy.yaml` exists with DoR/DoD rules

**When**: The user runs `specfact policy validate`

**Then**: The system loads policy config and applies rules; missing or invalid config is reported clearly

**Acceptance Criteria**:

- A project can define policies in `.specfact/policy.yaml`; loader does not crash on missing/invalid config.

### Requirement: Policy config scaffolding templates

The system SHALL provide a policy config scaffolding command that offers common framework templates and writes a starter `.specfact/policy.yaml` for user customization.

**Rationale**: Reduce setup friction and avoid manual YAML authoring errors.

#### Scenario: Interactive template selection

**Given**: A repository without `.specfact/policy.yaml`

**When**: The user runs `specfact policy init`

**Then**: The CLI prompts for a template/framework selection (for example Scrum, Kanban, SAFe, Mixed)

**And**: The selected template is written to `.specfact/policy.yaml`

**And**: The generated file is intended for further user adjustment.

#### Scenario: Non-interactive template selection

**Given**: A repository without `.specfact/policy.yaml`

**When**: The user runs `specfact policy init --template scrum`

**Then**: The Scrum template is written without interactive prompts.

**Acceptance Criteria**:

- Template catalog includes the most common supported frameworks (Scrum, Kanban, SAFe, Mixed baseline).
- Built-in template sources are loaded from `resources/templates/policies/` so they are packaged with SpecFact distributions.
- Generated policy file is valid YAML and can be consumed by `specfact policy validate`.

### Requirement: Policy validate docs hints

The system SHALL provide actionable format/documentation hints when `specfact policy validate` detects missing or invalid policy config.

**Rationale**: Improve self-service troubleshooting.

#### Scenario: Missing config points to docs

**Given**: `.specfact/policy.yaml` is missing

**When**: The user runs `specfact policy validate`

**Then**: The error explains the expected config location

**And**: The output includes a hint to the policy config format documentation.

#### Scenario: Invalid config points to docs

**Given**: `.specfact/policy.yaml` exists but is malformed or does not follow expected schema

**When**: The user runs `specfact policy validate`

**Then**: The error includes the parse/validation failure reason

**And**: The output includes a hint to the policy config format documentation.
