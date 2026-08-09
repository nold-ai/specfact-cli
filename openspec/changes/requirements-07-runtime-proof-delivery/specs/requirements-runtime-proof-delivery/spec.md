## ADDED Requirements

### Requirement: Lifecycle-Derived Requirements Gate

Core SHALL derive the required evidence maturity from the complete pull-request
or staged diff and repository policy rather than an author-declared phase. A
proposal-only change requires `planned` maturity and may pass without test
execution; its retained report SHALL explicitly state that implementation
evidence is not yet available. Test-only and production changes SHALL require
successively stronger accepted, red, and verified evidence.

#### Scenario: Proposal-only change passes readiness without execution

- **GIVEN** a changed OpenSpec proposal with a complete planned requirements
  mapping and no changed governed production or test path
- **WHEN** the gate evaluates the diff
- **THEN** it requires `planned` maturity
- **AND** it publishes a successful proposal-readiness report
- **AND** the report labels implementation evidence as not-yet-available
- **AND** it does not label the change executed, implemented, or verified.

#### Scenario: Mixed or production diff cannot be downgraded

- **GIVEN** a diff containing a proposal mapping and a governed test or
  production touchpoint
- **WHEN** the gate evaluates the diff
- **THEN** it requires the strongest maturity applicable to that touchpoint
- **AND** a proposal-only mapping cannot cause the product change to pass at
  `planned` maturity.

### Requirement: Accepted Mapping Before Automation

Core SHALL require acceptance evidence bound to the canonical mapping digest
before test automation or production implementation. Acceptance may originate
from a trusted reviewed base branch or a provider-neutral normalized review
record; proposal-only readiness SHALL expose pending acceptance without
blocking proposal review.

#### Scenario: Test-only change requires current acceptance

- **GIVEN** a test-only diff mapped to an active requirement source
- **WHEN** the gate evaluates the diff
- **THEN** it requires accepted mapping evidence whose digest matches the
  current mapping
- **AND** stale, rejected, or unverifiable review evidence blocks automation.

### Requirement: Git-Bound Failing-First Proof

Core SHALL require a runner-generated red proof from a test-only ancestor
commit after the current pull-request base before a governed production change
can reach verified maturity. The
proof SHALL bind the commit/tree, merge base, mapping digest, selectors,
test-file digests, JUnit digest, and toolchain identity. Core SHALL reject
proof when governed production changed before the red commit, including a
governed source renamed outside its prefix, or when selectors or test files
changed after it. Before forwarding a prior-red report to the
released reconciliation command, core SHALL verify that its source commit is a
strict ancestor of the final source, the current pull-request base is an
ancestor of that source, and that the selected test files remain
unchanged since that source.

#### Scenario: Production change follows valid red proof

- **GIVEN** a valid test-only ancestor and red proof for the exact mapping and
  selectors
- **WHEN** production code changes and the selectors pass at the current HEAD
- **THEN** the gate reports verified maturity
- **AND** it preserves both red and final execution provenance.

#### Scenario: Same-commit or stale red proof is rejected

- **GIVEN** tests and production code first appear in the same commit, or a
  mapped selector/test file changes after the red proof
- **WHEN** the gate evaluates a governed production diff
- **THEN** it fails with `tdd-order-unproven` or `stale-red-proof`
- **AND** it retains diagnostic artifacts before enforcing the verdict.

### Requirement: Staged Scenario Proof Planning

The core pre-commit gate SHALL invoke only a verified released Requirements
module to produce and validate a proof plan from the staged Git index before
Code Review and contract tests. It SHALL keep local planning bounded and SHALL
NOT claim current-run execution proof without a result-reconciliation step.

#### Scenario: Staged product change has complete proof plan

- **GIVEN** staged requirement and product-interface changes map selected
  scenarios to valid touchpoints and exact test selectors
- **WHEN** pre-commit Block 2 runs
- **THEN** the gate retains the index-isolated plan and static evidence report
- **AND** it continues to ordinary Code Review and contract gates
- **AND** it does not mark any test executed or passed.

#### Scenario: Staged interface change lacks mapped proof

- **GIVEN** a staged relevant product-interface change with no governed
  scenario mapping or no valid exact test selector
- **WHEN** staged proof planning runs under strict policy
- **THEN** the gate retains remediation evidence and exits non-zero
- **AND** later review and contract gates do not run.

#### Scenario: Staged change has no requirement impact

- **GIVEN** the staged diff qualifies for a governed no-requirement-impact
  decision
- **WHEN** planning runs
- **THEN** it emits an explicit skipped report with the bounded reason and
  changed-path digest
- **AND** policy-designated product-interface, contract, requirement-source,
  and proof-test paths cannot use that skip
- **AND** it does not silently omit the Requirements gate.

### Requirement: Safe Pull-Request Proof Execution

Core CI SHALL validate a module-produced structured proof plan and execute only
supported exact test selectors in the frozen repository environment. It SHALL
pass selectors as process arguments without shell interpretation and SHALL
retain deterministic JUnit results for module-owned reconciliation.

#### Scenario: Valid exact selectors execute through an argument array

- **GIVEN** the verified module emits a supported bounded plan whose pytest
  selectors identify repository-contained exact test cases
- **WHEN** the CI executor runs the plan
- **THEN** it invokes the frozen pytest runner with selectors as argument-array
  values after the runner option boundary
- **AND** a repository-controlled result plugin records each exact collected
  pytest node ID as a canonical selector property in JUnit
- **AND** it writes JUnit to a fresh deterministic artifact path
- **AND** it does not use `eval`, shell expansion, or command text from the plan.

#### Scenario: Unsafe plan is rejected before test execution

- **GIVEN** a selector has an absolute or escaping path, option prefix,
  control/shell syntax, wildcard expansion, duplicate identity, unsupported
  runner, or exceeds a configured plan bound
- **WHEN** core validates the plan
- **THEN** it fails before starting a test process
- **AND** it retains bounded diagnostic evidence describing the rejected field.

#### Scenario: Test execution is incomplete or fails

- **GIVEN** a valid plan whose test process times out, fails, errors, skips a
  required test, or omits a required selector from JUnit
- **WHEN** core returns the plan and available JUnit to the verified module
- **THEN** the module-owned final report remains red or unproven
- **AND** core publishes all available artifacts before enforcing failure.

### Requirement: Authoritative Reconciliation and Review Handoff

Core SHALL delegate scenario proof reconciliation to the same verified module
release that produced the plan. It SHALL pass only finalized Requirements proof
to the released Code Review context interface, preserve both reports and
verdicts separately, and run existing contract/full quality gates independently.

#### Scenario: Current-run proof passes and informs review

- **GIVEN** exact selected tests execute and pass and module reconciliation
  returns a finalized passing Requirements report
- **WHEN** CI starts Code Review
- **THEN** it supplies the finalized report as validated context
- **AND** retains Requirements and review provenance separately
- **AND** continues to existing independent contract and quality checks.

#### Scenario: Review passes while Requirements proof fails

- **GIVEN** the Requirements report is red and the separate review report is
  green
- **WHEN** delivery enforcement runs
- **THEN** the Requirements check remains blocking
- **AND** the review verdict does not replace or rewrite it.

#### Scenario: Requirements proof passes while another gate fails

- **GIVEN** the Requirements report is green but Code Review, contract tests,
  full tests, static analysis, or security checks fail
- **WHEN** delivery enforcement completes
- **THEN** those independent gates remain blocking
- **AND** targeted scenario proof is not treated as a replacement for them.

### Requirement: Always-Published Requirements Proof Decision

Pull-request CI SHALL produce a selected, failed, or explicit skipped
Requirements proof decision for every governed pull request and SHALL retain
the plan, JUnit when execution starts, final JSON/Markdown evidence, and concise
summary before enforcing a red verdict.

#### Scenario: Relevant product change cannot disappear through path filters

- **GIVEN** a pull request changes governed product, contract, test, or
  requirement-source paths
- **WHEN** workflows are scheduled
- **THEN** the Requirements proof decision runs even if no OpenSpec file changed
- **AND** branch protection receives a terminal result.

#### Scenario: No-impact pull request reports a governed skip

- **GIVEN** a pull request has no requirement impact under deterministic policy
- **WHEN** the Requirements proof decision runs
- **THEN** it publishes a skipped report and reason
- **AND** branch protection receives a successful terminal result rather than a
  missing check.
