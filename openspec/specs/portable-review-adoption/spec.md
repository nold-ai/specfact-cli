# portable-review-adoption Specification

## Purpose
TBD - created by archiving change code-review-09-f4-automation-upgrade. Update Purpose after archive.
## Requirements
### Requirement: Portable Review-Gate Adoption Guidance
The system SHALL document how to add the same `specfact code review run`
pre-commit gate to other projects, including optional house-rules workflow
usage and the default local JSON ledger behavior with optional configured
backend support.

#### Scenario: Documentation shows a reusable pre-commit configuration
- **GIVEN** a developer wants to add code review gating to another project
- **WHEN** they read the code-review module documentation
- **THEN** they can copy a concrete pre-commit configuration that runs `specfact code review run` before commit success

#### Scenario: Documentation explains optional house-rules integration
- **GIVEN** a project maintains a `house_rules` skill file
- **WHEN** the developer follows the adoption guidance
- **THEN** the documentation explains how to use that guidance in the review workflow without making it mandatory

#### Scenario: Documentation explains JSON-first ledger behavior
- **GIVEN** a developer uses the review gate on a local or offline project
- **WHEN** they read the adoption guidance
- **THEN** the documentation states that the ledger works with local JSON storage by default and may use Supabase or another backend only when configured

#### Scenario: Documentation explains commit-blocking semantics
- **GIVEN** a developer adopts the review gate in another repository
- **WHEN** they read the guidance
- **THEN** they understand that only blocking review verdicts fail the commit while advisory verdicts remain commit-green

