## ADDED Requirements

### Requirement: Required checks trigger for every supported pull request

Docs Review and SpecFact CLI Validation SHALL use native pull-request triggers for every pull request targeting `main` or `dev`, without workflow-level path inclusion or exclusion filters. Their existing required jobs SHALL remain scheduled without a job-level condition. Existing push filters and validation behavior SHALL remain unchanged.

#### Scenario: Docs check remains available for ancestry-only changes

- **GIVEN** an ancestry-only pull request targeting `dev` or `main`
- **WHEN** GitHub evaluates the Docs Review pull-request trigger
- **THEN** no path filter suppresses the workflow
- **AND** the existing Docs Review job and push path inclusion list remain intact

#### Scenario: Contract check remains available for documentation-only changes

- **GIVEN** a documentation-only pull request targeting `dev` or `main`
- **WHEN** GitHub evaluates the SpecFact CLI Validation pull-request trigger
- **THEN** no ignored-path filter suppresses the workflow
- **AND** the existing Contract Validation job and push path exclusion list remain intact
