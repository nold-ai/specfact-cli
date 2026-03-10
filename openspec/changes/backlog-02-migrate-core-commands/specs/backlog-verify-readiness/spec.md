# backlog-verify-readiness Specification

## ADDED Requirements

### Requirement: Restore Definition of Ready validation

The system SHALL provide `specfact backlog verify-readiness` for DoR validation.

#### Scenario: Verify-readiness checks DoR criteria
- **WHEN** the user runs `specfact backlog verify-readiness --project-id <id>`
- **THEN** each backlog item is validated against `.specfact/dor.yaml`
- **AND** items passing/failing DoR are reported

#### Scenario: DoR failures show actionable guidance
- **WHEN** an item fails DoR validation
- **THEN** specific missing criteria are listed
- **AND** remediation hints are provided
