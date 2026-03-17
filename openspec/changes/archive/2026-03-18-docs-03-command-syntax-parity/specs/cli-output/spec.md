## MODIFIED Requirements

### Requirement: Command Reference Completeness

The system SHALL keep authored docs parity validation aligned with the shipped CLI command surfaces for each release, including checks that removed command-syntax families stay absent from authored docs.

#### Scenario: Docs parity checks run after command-surface changes

- **GIVEN** authored docs contain user-facing command examples in `README.md` and `docs/`
- **WHEN** docs parity validation runs for a release
- **THEN** validation fails if authored docs still reference removed or transitional syntax families such as `project plan`, `project import from-bridge`, `backlog policy`, or retired `spec` subgroup trees
- **AND** validation passes only when current docs examples align with the shipped command groups and the supported parameter forms documented for that release
