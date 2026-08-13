## MODIFIED Requirements

### Requirement: Requirements evidence delivery enforcement

The core CLI SHALL enforce the reviewed, immutable Requirements module release before Code Review and contract delivery gates. It SHALL verify the exact fixture identity before module execution, invoke released commands through an explicit non-secret environment allowlist, retain every current-run Requirements artifact produced by the reached stages, and enforce Requirements and Code Review decisions independently.

#### Scenario: Reject an unverified or mutable fixture

- **GIVEN** the modules repository, commit, tree, package version, signature, accepted report-schema version, or clean-state identity differs from the fixture lock
- **WHEN** local or CI Requirements evidence enforcement initializes
- **THEN** it fails before invoking module code
- **AND** it does not use a branch, sibling checkout, or other mutable module source
- **AND** it retains an actionable fixture diagnostic.

#### Scenario: Exclude ambient secrets from released execution

- **GIVEN** the caller environment contains permitted runtime variables and unrelated secret-like variables
- **WHEN** core invokes a released Requirements planning or reconciliation command
- **THEN** only the explicit non-secret runtime allowlist and verified fixture-root variables are present
- **AND** unrelated ambient variables and caller-controlled `PYTHONPATH` are absent.

#### Scenario: Block staged delivery after retaining a red report

- **GIVEN** the verified released fixture returns a blocking or unresolved staged Requirements decision
- **WHEN** the pre-commit hook evaluates staged changes
- **THEN** it retains the JSON and Markdown remediation reports before returning non-zero
- **AND** Code Review and contract-test gates do not run afterward.

#### Scenario: Continue staged delivery after a green report

- **GIVEN** the verified released fixture returns a non-blocking staged Requirements decision
- **WHEN** the pre-commit hook evaluates staged changes
- **THEN** it retains the generated reports
- **AND** it continues to the existing Code Review and contract-test gates.

#### Scenario: Publish pull-request evidence for any verdict

- **GIVEN** planning or execution produces success, failure, timeout, or reconciliation diagnostics
- **WHEN** the pull-request workflow reaches its terminal policy step
- **THEN** it has already uploaded the plan, JUnit when produced, Requirements JSON and Markdown, and Code Review JSON when review execution is reached
- **AND** the summary identifies which independent claim failed or remained unresolved
- **AND** a blocking verdict fails delivery only after its available artifacts are retained.

#### Scenario: Review is run over an explicit resolved file set

- **GIVEN** the workflow invokes Code Review after Requirements reconciliation
- **WHEN** it selects review targets
- **THEN** it passes an explicit PR-delta file set or uses the module's explicit base/head range interface
- **AND** it does not rely on a clean checkout's worktree-only changed scope
- **AND** generic Code Review scope semantics remain module-owned.

#### Scenario: Independent failures remain blocking

- **GIVEN** Requirements passes but Code Review fails, or Code Review passes but Requirements fails
- **WHEN** the terminal policy step runs
- **THEN** the workflow exits non-zero
- **AND** neither green signal overwrites the failing signal.
