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
