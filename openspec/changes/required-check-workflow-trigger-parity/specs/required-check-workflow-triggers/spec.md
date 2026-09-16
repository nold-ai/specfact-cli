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

#### Scenario: Fork pull requests retain usable contract validation

- **GIVEN** a pull request from a fork with a read-only workflow token
- **WHEN** Contract Validation produces a report
- **THEN** the optional repository comment is not posted with that token
- **AND** validation, report artifacts, and the existing failure gate still run

#### Scenario: Complete push filter lists remain unchanged

- **GIVEN** the complete established push filter lists for both required workflows
- **WHEN** the pull-request trigger fix is reviewed
- **THEN** regression checks reject any added or removed push pattern, including patterns beyond the original representative subset

#### Scenario: Same-repository read-only tokens cannot fail optional comments

- **GIVEN** a same-repository pull request whose token cannot create a comment, including a Dependabot event
- **WHEN** the optional comment API returns HTTP 403
- **THEN** the awaited request is handled with a visible warning
- **AND** validation and its existing failure policy remain authoritative
- **AND** successful requests complete normally while non-permission API failures remain visible as errors
