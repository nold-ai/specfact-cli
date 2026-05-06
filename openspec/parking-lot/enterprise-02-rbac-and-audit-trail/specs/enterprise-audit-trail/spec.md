## ADDED Requirements

### Requirement: Enterprise Role Vocabulary

The system SHALL define enterprise roles `org-admin`, `team-lead`, `developer`, and `auditor` for client-side governance actions.

#### Scenario: Unknown role is rejected

- **WHEN** an enterprise action references a role outside the canonical set
- **THEN** validation fails before the action is persisted or transmitted.

#### Scenario: Roles can be attached to audited actions

- **WHEN** an enterprise-sensitive action is recorded
- **THEN** the acting role is captured as part of the audit event
- **AND** downstream consumers can distinguish admin, lead, developer, and auditor actions.

### Requirement: Signed Audit Event Schema

The system SHALL persist signed audit events for enterprise-sensitive actions.

#### Scenario: Audit event records provenance

- **WHEN** a pushed rule, override, approval, or telemetry preference change is recorded
- **THEN** the event includes actor, role, action, target scope, timestamp, and signature metadata
- **AND** the record is append-only.

#### Scenario: Audit event can link to evidence

- **GIVEN** an audited action has related governance or FinOps evidence
- **WHEN** the audit event is written
- **THEN** it may include linked evidence identifiers
- **AND** those identifiers are structured, not free-form payload copies.
