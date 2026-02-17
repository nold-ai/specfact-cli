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

### Requirement: Policy suggest (AI-assisted, patch-ready)

The system SHALL provide `specfact policy suggest` that proposes fixes with confidence scores and patch-ready output when applicable; user confirmation required before apply.

**Rationale**: Plan Δ1—actionable suggestions without silent writes.

#### Scenario: Suggest policy fixes

**Given**: Policy validate has reported failures

**When**: The user runs `specfact policy suggest`

**Then**: The system proposes fixes (e.g. missing fields, DoR gaps) with confidence and optional patch; no write without explicit user action

**Acceptance Criteria**:

- Suggestions are confidence-scored and patch-ready; no automatic writes.

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
