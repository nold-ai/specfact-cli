## Scope rescope — 2026-09-20

Seal, checkpoint, frozen mapping, successor approval, and historical RED/GREEN requirements in this issue apply only when an explicitly selected assurance policy requests them. They are not prerequisites for ordinary implementation, Code Review, release promotion, skill installation, or generated instructions. Keep the internal optional-feature dependency chain and source/signature integrity. Missing optional chronology is not a failed current-execution claim. No runtime policy changes in this planning update. The dogfood exercise requires both core C14 #680 and modules runtime #431; record both native prerequisites now that C14 no longer depends on #431.

This owner-requested scope amendment takes precedence over conflicting default-workflow or dependency wording below. It changes planning only; runtime policy is unchanged. [Replacement policy](../../../requirements-09-minimal-evidence/proposal.md).

## ADDED Requirements

### Requirement: Identity-bound C14 dogfood run

These assurance obligations SHALL apply only when an explicitly selected
preflight assurance policy requests them; they SHALL NOT gate ordinary MEB delivery.

The dogfood protocol SHALL run the exact preflight workflow against core C14 issue #680 and an immutable planning snapshot after its independent delivery using recorded repository, issue, dependency, validator, and source identities.

#### Scenario: Ordinary delivery has not selected preflight assurance

- **GIVEN** ordinary MEB delivery has not selected a preflight assurance policy
- **WHEN** implementation or delivery readiness is evaluated
- **THEN** no preflight seal, checkpoint, successor approval, or historical chronology is required
- **AND** required current checks still apply, without claiming that unevaluated optional assurance passed.

#### Scenario: Initial dogfood snapshot is captured

- **GIVEN** C14 has been independently delivered and its immutable planning snapshot is selected for review replay without concurrent ownership ambiguity
- **WHEN** dogfood begins
- **THEN** the starting source identities and expected-risk inventory are recorded before refinement
- **AND** the C14 implementation worktree is not modified by the dogfood setup.

### Requirement: User-authorized refinement only

The dogfood protocol SHALL separate tool findings from source changes and SHALL require the owning user/session to authorize every material refinement. Replay refinements SHALL change only the selected fixture; real product corrections require separately scoped follow-ups and SHALL NOT rewrite shipped C14 history.

#### Scenario: Finding requires C14 scope clarification

- **GIVEN** preflight reports a blocking scope ambiguity in C14
- **WHEN** the dogfood operator reviews the finding
- **THEN** the exact owning artifact and proposed clarification are presented to the C14 owner
- **AND** no edit, approval, or seal occurs until that owner authorizes the change.

#### Scenario: Authorized C14 artifact changes

- **GIVEN** the C14 owner authorizes a refinement of the selected replay fixture
- **WHEN** dogfood resumes
- **THEN** all prior readiness and approval state is discarded
- **AND** a new snapshot and complete validator run are required.

### Requirement: Defect ownership classification

Every dogfood observation SHALL be assigned to core contract, modules runtime, source artifact/metadata, instruction/guidance, or explicit unknown ownership.

#### Scenario: Observation cannot be attributed

- **GIVEN** evidence does not distinguish a validator defect from an invalid source artifact
- **WHEN** the observation is recorded
- **THEN** ownership is `UNKNOWN`
- **AND** the observation cannot justify an implementation task until discriminating evidence is captured.

### Requirement: Readiness decision criteria

These assurance obligations SHALL apply only when an explicitly selected
preflight assurance policy requests them; they SHALL NOT gate ordinary MEB delivery.

The core dogfood change SHALL emit a go/no-go decision for modules hardening based on deterministic completion, approval safety, stale-input invalidation, renderer parity, and evidence-backed issue classification.

#### Scenario: Readiness criteria fail

- **GIVEN** a required validator is indeterminate, an unapproved edit occurred, a stale seal verifies, or human/JSON results disagree
- **WHEN** readiness is decided
- **THEN** the decision is no-go
- **AND** the paired modules hardening/publication change remains blocked.

#### Scenario: Bounded readiness criteria pass

- **GIVEN** every required criterion passes on the final identity-bound C14 run
- **WHEN** readiness is decided
- **THEN** the decision may authorize the paired modules hardening phase
- **AND** it states that one dogfood target does not prove universal correctness.

### Requirement: Evidence-backed hardening handoff

Every proposed hardening item SHALL cite an observed run, finding, affected contract path, generalized rule, regression case, and owning repository.

#### Scenario: Suggested improvement lacks evidence

- **GIVEN** a possible enhancement was not observed and is not required by the approved contract
- **WHEN** the handoff is assembled
- **THEN** it is excluded from the blocking hardening scope
- **AND** may be recorded separately as a hypothesis or follow-up.
