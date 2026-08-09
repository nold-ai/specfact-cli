## MODIFIED Requirements

### Requirement: Requirements evidence delivery enforcement

The core CLI SHALL enforce the released Requirements evidence command before
code-review and contract delivery gates, using only a SHA-pinned
`nold-ai/specfact-cli-modules` fixture at
`69f075819be5e1ceca1446b026b0417f19e584ca`. Core SHALL preserve the
module-owned evidence semantics and SHALL retain JSON and Markdown remediation
reports for both passing and failing runs.
Core SHALL pass the released command only an explicit non-secret environment
allowlist plus the two fixture-root variables required for module discovery.
Pull-request workflow invocations of both evidence and reconciliation SHALL use
the same explicit environment boundary.

#### Scenario: Reject an unverified or mutable fixture

- **GIVEN** the fixture lock is absent, malformed, points outside
  `nold-ai/specfact-cli-modules`, names any commit other than
  `69f075819be5e1ceca1446b026b0417f19e584ca`, does not match the materialized
  commit, or materializes a dirty worktree
- **WHEN** local or CI requirements evidence enforcement starts
- **THEN** it fails before executing any module command
- **AND** it does not use a branch, sibling checkout, or other mutable source
- **AND** it reports how to obtain the released pinned fixture.

The fixture trust boundary is the immutable, reviewed commit and tree
attestation recorded in the checked-in lock and materialized by GitHub
checkout. Core SHALL verify both identities before execution.

#### Scenario: Exclude ambient secrets from released execution

- **GIVEN** the caller environment contains permitted runtime variables and
  unrelated secret-like variables
- **WHEN** core invokes the released Requirements evidence command
- **THEN** permitted runtime variables and the verified fixture roots are present
- **AND** unrelated ambient variables and caller-controlled `PYTHONPATH` are absent.

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

#### Scenario: Reconcile the approved historical R07 ledger without synthetic red proof

- **GIVEN** the selected change is `requirements-07-runtime-proof-delivery`,
  the approved immutable commit contains its historical failing-first ledger,
  and the released module produces a final proof plan
- **WHEN** core reconciles the current JUnit result
- **THEN** it reads and hashes the ledger from that approved commit and passes a
  digest-bound
  `legacy-tdd-ledger` record with the plan and mapping digests to final
  reconciliation
- **AND** a modified pull-request checkout ledger cannot satisfy the exception
- **AND** it does not create or pass a synthetic `red.json`
- **AND** ordinary changes continue to require the normal red-JUnit proof.

#### Scenario: Review only existing Python paths with finalized proof context

- **GIVEN** final Requirements reconciliation succeeds and the pull-request
  diff includes deleted Python paths
- **WHEN** CI invokes Code Review with the finalized Requirements JSON
- **THEN** it passes only still-existing Python paths to the review command
- **AND** it applies full enforcement to those explicitly diff-selected paths
- **AND** it retains the separate Code Review report before independently
  enforcing a failed review verdict.

#### Scenario: Runtime smoke registry includes declared bundle dependencies

- **GIVEN** a root module exercised by the runtime-discovery smoke check
  declares one or more transitive `bundle_dependencies`
- **WHEN** core builds the smoke check's isolated local registry
- **THEN** it includes each declared dependency exactly once before a launcher
  attempts marketplace installation
- **AND** it fails fixture assembly for malformed or missing dependency
  metadata rather than reporting a false runtime-resolution failure.

#### Scenario: Runtime smoke registry accepts only semantic module versions

- **GIVEN** a module manifest used to assemble the isolated smoke registry
- **WHEN** core validates its version before creating the module archive
- **THEN** it accepts the complete Semantic Versioning 2.0.0 grammar
- **AND** it rejects leading zeroes in numeric core or prerelease identifiers,
  empty identifiers, and other malformed versions before writing an archive.
