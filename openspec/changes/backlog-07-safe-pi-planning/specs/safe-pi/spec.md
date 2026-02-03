# SAFe PI Planning (PI summary, WSJF, PI readiness)

## ADDED Requirements

### Requirement: backlog pi-summary command

The system SHALL provide `specfact backlog pi-summary` that outputs PI-level summary: PI scope, team commitments, cross-team dependency contracts, ROAM items (when available from dependency analysis).

**Rationale**: Δ5—SAFe-first workflow.

#### Scenario: Run pi-summary

**Given**: A project with backlog adapter and optional `.specfact/safe.yaml` and dependency/ROAM data (#116)

**When**: The user runs `specfact backlog pi-summary`

**Then**: The system outputs PI scope, commitments, dependency contracts, and ROAM items when available

**And**: Output is available in JSON and Markdown

**And**: PI summary SHALL include a ROAM-ready Markdown table (e.g. risks/obstacles/assumptions/mitigations) when ROAM data is available

**Acceptance Criteria**:

- Command runs without error; output includes PI scope and (when data exists) commitments, dependency contracts, ROAM.
- PI summary includes a ROAM-ready Markdown table when ROAM data is available.

### Requirement: SAFe config and PI readiness

The system SHALL support `.specfact/safe.yaml` for PI/iteration/ART settings. Config SHALL integrate with Policy Engine (#176) for PI readiness policy hooks.

**Rationale**: Δ5—config-driven SAFe behavior.

#### Scenario: Load safe config

**Given**: `.specfact/safe.yaml` exists with PI/iteration settings

**When**: The user runs `specfact backlog pi-summary` or Policy Engine validates PI readiness

**Then**: The system loads safe config and applies PI readiness rules; missing config is handled gracefully

**Acceptance Criteria**:

- Config is optional; Policy Engine can use PI readiness policy when config present.

### Requirement: WSJF assistance

The system SHALL provide WSJF calculation with AI-assisted missing-field proposals and user confirmation; output as JSON and Markdown. No automatic write without confirmation.

**Rationale**: Δ5—WSJF for prioritization without silent writes.

#### Scenario: WSJF with missing fields

**Given**: User requests WSJF for a set of items with some missing WSJF fields

**When**: The system runs WSJF assistance

**Then**: The system proposes missing field values (e.g. job size, value) with confidence; user confirms before apply

**And**: Output includes WSJF score and optional patch for fields

**Acceptance Criteria**:

- WSJF calculation is deterministic when fields present; AI-assisted proposals require confirmation; no silent writes.
- WSJF AI-assisted field proposals are applied only with explicit user confirmation or when user invokes with `--write` (per patch-mode / write gating); AI proposals never write fields without `--write`.
