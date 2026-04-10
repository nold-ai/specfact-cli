# adr-template Specification

Architecture Decision Records (ADRs) are available so that major architectural decisions are recorded and discoverable.

## ADDED Requirements

### Requirement: ADR template exists

The docs SHALL provide an ADR template with at least: title, status, context, decision, consequences.

#### Scenario: Maintainer records new decision

- **GIVEN** the docs repository
- **WHEN** a maintainer wants to record a new architectural decision
- **THEN** an ADR template exists (e.g. in docs/architecture/adr/template.md)
- **AND** the template includes title, status, context, decision, consequences

### Requirement: At least one ADR present

The ADR directory SHALL contain at least one ADR (e.g. for module-first architecture) following the template.

#### Scenario: Reader opens architecture docs

- **GIVEN** the ADR directory
- **WHEN** a reader opens the architecture documentation
- **THEN** at least one ADR is present following the template
- **AND** it documents a major architectural decision

### Requirement: ADRs discoverable from docs

ADRs SHALL be linked from docs/architecture/README.md or docs/reference/architecture.md so they can be found without searching the repo.

#### Scenario: User navigates architecture docs

- **GIVEN** the docs site (e.g. docs.specfact.io)
- **WHEN** a user navigates architecture or reference docs
- **THEN** ADRs are linked
- **AND** discoverable from the menu or architecture index
