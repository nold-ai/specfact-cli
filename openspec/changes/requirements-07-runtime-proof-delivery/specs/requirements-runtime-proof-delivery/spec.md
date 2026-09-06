## ADDED Requirements

### Requirement: Lifecycle-Derived Requirements Gate

Core SHALL derive required evidence maturity from the evaluated staged or pull-request snapshot and repository policy. Proposal readiness, accepted mapping, current execution, and historical red-green chronology are separate claims. A weaker artifact SHALL NOT downgrade a stronger maturity required by changed governed paths.

#### Scenario: Proposal-only change reports readiness without execution

- **GIVEN** only proposal artifacts changed and their planned mappings are complete
- **WHEN** the Requirements gate evaluates the snapshot
- **THEN** it may pass proposal readiness
- **AND** it reports implementation evidence as not yet available
- **AND** it makes no current-run or historical proof claim.

#### Scenario: Production change cannot be downgraded by proposal files

- **GIVEN** a snapshot changes both proposal files and governed production touchpoints
- **WHEN** maturity is derived
- **THEN** the strongest applicable maturity is required
- **AND** an author-provided phase label cannot reduce it.

### Requirement: Accepted Mapping Before Automation

Core SHALL require the pinned Requirements module to validate provider-neutral acceptance evidence against the current mapping digest before test-authored or current-run evidence can satisfy strict policy.

#### Scenario: Stale acceptance blocks automation

- **GIVEN** acceptance evidence is missing, rejected, or bound to another mapping digest
- **WHEN** the gate requires accepted maturity or higher
- **THEN** it preserves a deterministic acceptance finding
- **AND** it does not invent approval from passing tests.

### Requirement: Staged Scenario Proof Planning

The staged gate SHALL evaluate only the Git index, validate mapped touchpoints and exact structured selectors, and retain a plan or explicit no-impact decision. It SHALL NOT execute tests or reuse worktree/CI evidence for different bytes.

#### Scenario: Valid staged mapping produces a static plan

- **GIVEN** staged governed changes have accepted scenarios and safe exact selectors
- **WHEN** pre-commit planning runs
- **THEN** it emits an index-bound deterministic plan
- **AND** it does not claim collection, execution, pass, or red-green chronology.

#### Scenario: Unmapped staged interface blocks later gates

- **GIVEN** a staged governed interface has no accepted scenario or exact selector when required
- **WHEN** planning runs
- **THEN** the gate retains remediation evidence and fails before review and contract gates.

### Requirement: Safe Pull-Request Proof Execution

Core SHALL execute only exact selectors from a validated plan by using a subprocess argument array in a pinned, bounded environment. It SHALL reject unsafe selectors, unsupported runners, excessive plans, missing regular files, and incomplete result output before current-run proof can pass.

#### Scenario: Exact selectors produce canonical JUnit identities

- **GIVEN** a valid current-run plan
- **WHEN** core invokes pytest
- **THEN** selectors appear only after the option boundary in the argument array
- **AND** every collected test case records its canonical selector identity
- **AND** the JUnit artifact is written outside mutable source paths.

#### Scenario: Unsafe input fails before execution

- **GIVEN** a selector contains traversal, absolute paths, option/control syntax, shell syntax, wildcard expansion, duplication, or an unsupported runner
- **WHEN** the executor validates the plan
- **THEN** it emits a bounded failure and starts no test process.

#### Scenario: Missing or incomplete JUnit is not a pass

- **GIVEN** the executor times out, errors, emits no non-empty JUnit, or fails to collect every selector exactly once
- **WHEN** the gate finalizes current-run evidence
- **THEN** the execution claim is failed or unknown according to module policy
- **AND** it is never converted to pass or no-impact.

### Requirement: Current-Run Evidence Boundary

Core SHALL report exact-selector execution observed in the current run independently from any historical failing-first claim. A current-run result SHALL bind the mapping, plan, selectors, source commit and tree, JUnit digest, runner identity, environment identity, and collection/result counts.

#### Scenario: Current selectors pass without historical proof

- **GIVEN** every required selector is collected exactly once and passes at the evaluated source
- **WHEN** the pinned module reconciles the current-run plan and JUnit
- **THEN** the report records a passing current execution
- **AND** it does not label the result passing-after-red or change-proven
- **AND** a missing historical attestation leaves only the independent chronology claim unproven.

#### Scenario: Historical evidence cannot inflate current execution

- **GIVEN** a retained historical artifact exists but current selectors are missing, skipped, failed, errored, or ambiguous
- **WHEN** reconciliation runs
- **THEN** current execution does not pass
- **AND** historical evidence cannot replace current-run results.

### Requirement: Authoritative Reconciliation and Review Handoff

Core SHALL delegate current-run reconciliation to the same pinned Requirements module release and pass the finalized result to Code Review only as validated context. Requirements, Code Review, contracts, security, and broader tests retain independent verdicts.

#### Scenario: Finalized evidence informs review without verdict fusion

- **GIVEN** a finalized current-run Requirements report
- **WHEN** Code Review receives it
- **THEN** review retains its source and digest provenance
- **AND** neither decision changes the other decision, score, or exit semantics.

### Requirement: Always-Published Requirements Proof Decision

Every governed pull request SHALL publish selected, failed, or deterministic no-impact Requirements evidence before enforcement. Scope-resolution failure, missing tools, timeout, or missing artifacts SHALL NOT be represented as no-impact or pass.

#### Scenario: Governed no-impact decision is auditable

- **GIVEN** the complete resolved PR diff contains no policy-governed Requirements impact
- **WHEN** the gate evaluates it
- **THEN** it publishes the base/head identities, changed-path digest, policy identity, and bounded reason
- **AND** the terminal check succeeds without claiming tests executed.

#### Scenario: Unresolved execution remains non-green

- **GIVEN** Git scope, the pinned fixture, a mandatory tool, execution, or an artifact cannot be resolved
- **WHEN** the terminal decision is produced
- **THEN** strict policy exits non-zero after retaining diagnostics
- **AND** no summary says all validations passed.

