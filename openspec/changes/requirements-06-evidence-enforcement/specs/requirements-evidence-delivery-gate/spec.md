## ADDED Requirements

### Requirement: Requirements evidence delivery enforcement

The core CLI SHALL enforce the released Requirements evidence command before
code-review and contract delivery gates, using only a SHA-pinned
`nold-ai/specfact-cli-modules` fixture. Core SHALL preserve the module-owned
evidence semantics and SHALL retain JSON and Markdown remediation reports for
both passing and failing runs.

#### Scenario: Reject an unverified or mutable fixture

- **GIVEN** the fixture lock is absent, malformed, points outside the approved
  modules repository, or does not match the materialized commit
- **WHEN** local or CI requirements evidence enforcement starts
- **THEN** it fails before executing any module command
- **AND** it does not use a branch, sibling checkout, or other mutable source
- **AND** it reports how to obtain the released pinned fixture.

#### Scenario: Block staged delivery after retaining a red report

- **GIVEN** the verified released fixture returns a red staged-evidence verdict
- **WHEN** the pre-commit hook evaluates staged changes
- **THEN** it retains the JSON and Markdown remediation reports at documented
  local paths before returning non-zero
- **AND** code-review and contract-test gates do not run afterward.

#### Scenario: Continue staged delivery after a green report

- **GIVEN** the verified released fixture returns a green staged-evidence verdict
- **WHEN** the pre-commit hook evaluates staged changes
- **THEN** it retains the generated reports
- **AND** it continues to the existing code-review and contract-test gates.

#### Scenario: Publish pull-request evidence for any verdict

- **GIVEN** a pull-request workflow evaluates Requirements evidence with a
  verified released fixture and pull-request base reference
- **WHEN** the command returns a green or red verdict
- **THEN** CI writes a concise job summary and uploads the JSON and Markdown
  reports
- **AND** a red verdict fails the delivery gate only after its reports are
  available.
