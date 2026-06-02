## ADDED Requirements

### Requirement: Review report documentation stays compatible with module-owned extensions

Core documentation that summarizes `ReviewReport` SHALL acknowledge additive module-owned fields without duplicating the full module schema.

#### Scenario: Report examples mention additive cleanup fields

- **WHEN** core docs show or describe review JSON
- **THEN** they SHALL state that Code Review bundle versions may add cleanup forecast and remediation handoff fields
- **AND** they SHALL tell consumers to treat unknown fields as additive metadata rather than schema-breaking changes

### Requirement: Public metadata reinforces the AI-bloat defense hook

GitHub and package-facing metadata SHALL reinforce the same first-contact story used in the README and docs landing pages.

#### Scenario: Public metadata is aligned

- **WHEN** a user sees GitHub repository metadata, PyPI/package metadata, or docs site metadata before opening the README
- **THEN** that metadata SHALL emphasize AI-bloat defense, deterministic code review, cleanup forecasts, and spec/contract evidence
- **AND** it SHALL not use "Swiss-knife" wording as the primary product identity
