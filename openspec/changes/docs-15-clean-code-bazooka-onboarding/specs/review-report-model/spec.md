## MODIFIED Requirements

### Requirement: Review report documentation stays compatible with module-owned extensions

Core documentation that summarizes `ReviewReport` SHALL acknowledge additive module-owned fields without duplicating the full module schema.

#### Scenario: Report examples mention additive cleanup fields

- **WHEN** core docs show or describe review JSON
- **THEN** they SHALL state that Code Review bundle versions may add cleanup forecast and remediation handoff fields
- **AND** they SHALL tell consumers to treat unknown fields as additive metadata rather than schema-breaking changes
