## ADDED Requirements

### Requirement: Normalized preflight design contract

The system SHALL define a versioned preflight design contract that records the exact reviewed change identity, source identities, implementation-lineage identity and origin baseline, role-classified scope, component ownership, approved influence relationships or explicit no-impact dispositions, exclusions, assumptions, unknowns, dependencies, interfaces, acceptance criteria, risk dimensions, verification stages, test intent, risks, rollback intent, and approval policy. The first approved seal in an implementation lineage SHALL set the immutable origin repository plus full base commit/tree identities. Every successor seal for refinement or reapproval SHALL bind its predecessor seal and preserve that origin baseline even when its current reviewed source snapshot changes.

#### Scenario: Contract preserves source and scope identity

- **GIVEN** a change assembled from OpenSpec, repository governance, GitHub metadata, and repository state
- **WHEN** the design contract is normalized
- **THEN** every input is represented by a stable source kind, location, revision or digest, and loader identity
- **AND** in-scope and explicitly excluded work are distinct contract fields.

#### Scenario: Implementation scope is machine-selectable

- **GIVEN** a planned change will modify source, tests, documentation, generated output, or evidence
- **WHEN** the design contract is normalized
- **THEN** every governed path pattern has one of `source`, `test`, `docs`, `generated`, `evidence`, or `excluded` roles
- **AND** every source role identifies one component, bounded pytest targets for that component, and its approved influence relationships.

#### Scenario: Every non-excluded sealed input has an influence disposition

- **GIVEN** a contract includes a non-excluded `source`, `test`, `docs`, `generated`, or `evidence` path or a seal-bound test, dependency, policy, toolchain, or relevant configuration input
- **WHEN** the design contract is normalized
- **THEN** the input maps through approved influence relationships to every acceptance, risk, Requirements case, component target, review/evidence, and execution-stage obligation it can affect, or carries an explicit no-impact disposition with a non-empty rationale
- **AND** an absent, ambiguous, or contradictory mapping/disposition prevents the contract from becoming ready for approval.

#### Scenario: Reapproval preserves the implementation origin

- **GIVEN** implementation or failing-first test work has begun under an approved seal and a refinement requires reapproval
- **WHEN** a successor contract and seal are normalized
- **THEN** they bind the predecessor seal and retain the original implementation-lineage repository, base commit, and base tree
- **AND** the later reviewed source snapshot cannot reset or truncate the cumulative implementation comparison.

#### Scenario: Unknown information is not silently resolved

- **GIVEN** a dependency, interface, or acceptance criterion cannot be verified
- **WHEN** the contract is created
- **THEN** the uncertainty is recorded as an explicit unknown
- **AND** it is not converted into an assumption or successful validation result.

### Requirement: Seal-bound semantic verification intent

The system SHALL bind the closed semantic risk dimensions `boundary`, `malformed_or_missing_input`, `state_transition`, `idempotency`, `cache`, `error`, `status`, `timeout`, `unknown_precedence`, `path`, `repository_lifecycle`, `platform`, and `compatibility` plus existing Requirements verification-plan identities without defining a second test-selector contract. Every affected behavior or interface SHALL contain every closed dimension.

#### Scenario: Applicable risk dimension is covered

- **GIVEN** one of the closed risk dimensions applies to an affected behavior or interface
- **WHEN** its risk record is normalized
- **THEN** it is marked `covered` and references existing requirement, scenario, and verification-case identities
- **AND** it declares the earliest required stage from `slice`, `commit`, `prepush`, or `ci`.

#### Scenario: Planned verification case is sealable before test authoring

- **GIVEN** an applicable risk references a complete existing Requirements case at `planned` maturity with stable requirement/scenario/case identity, method, intent, observable, and declared touchpoints but no authored test
- **WHEN** the pre-implementation contract is normalized
- **THEN** it binds the existing Requirements planned mapping/plan and case identities without inventing an exact selector
- **AND** it records that test-authored maturity and selector reconciliation are required at the declared execution stage before production implementation proceeds.

#### Scenario: Risk dimension is not applicable

- **GIVEN** one closed risk dimension does not apply to an affected behavior
- **WHEN** the risk record is normalized
- **THEN** it is marked `not_applicable` with a non-empty rationale
- **AND** absence of a mapped test is not silently interpreted as coverage.

#### Scenario: Requirements plan identity changes

- **GIVEN** the contract references an existing Requirements mapping digest, plan digest, verification case, or exact pytest selector when test-authored maturity has been reached
- **WHEN** any referenced identity changes
- **THEN** the design-contract digest changes
- **AND** a prior approval seal no longer verifies.

#### Scenario: Planned case becomes test-authored

- **GIVEN** an initial seal binds a Requirements case at `planned` maturity without a selector
- **WHEN** failing-first test creation produces the Requirements-owned exact pytest selector and test-authored plan
- **THEN** preflight validates the same requirement/scenario/case, method, intent, observable, touchpoints, and declared stage against the new mapping/plan identities
- **AND** production implementation waits for explicit approval of a successor seal that preserves the implementation-lineage origin baseline.

#### Scenario: Checkpoint selects already sealed evidence

- **GIVEN** a valid test-authored successor seal binds Requirements mapping and plan digests plus exact requirement, scenario, verification-case, and pytest-selector identities
- **WHEN** a checkpoint selects a subset of those identities for its affected implementation slice
- **THEN** the selection does not change the sealed design contract
- **AND** adding, removing, replacing, or changing a bound identity requires a newly validated and approved seal.

### Requirement: Deterministic validation result

The system SHALL define a versioned validation result bound to one exact design-contract digest and one identified validator set.

#### Scenario: Required validator is incomplete

- **GIVEN** policy requires a validator for dependency, scope, or interface completeness
- **WHEN** that validator does not complete with a determinate outcome
- **THEN** the validation result records an unknown outcome
- **AND** readiness is not `READY`.

#### Scenario: Findings retain stable ownership and severity

- **GIVEN** validators identify blocking, advisory, and unknown findings
- **WHEN** the result is serialized
- **THEN** each finding carries a stable identifier, owning validator, severity, affected contract path, and remediation target
- **AND** ordering is deterministic.

### Requirement: Canonical digest semantics

The system SHALL define versioned canonical bytes for digesting preflight contracts and validation results.

#### Scenario: Semantically identical supported input is canonicalized

- **GIVEN** two supported documents contain identical values with non-semantic map-order differences
- **WHEN** canonical bytes and digests are computed
- **THEN** the canonical bytes and digests are identical.

#### Scenario: Bound content changes

- **GIVEN** a source identity, scope boundary, component or influence mapping, no-impact disposition, risk record, Requirements plan identity, acceptance criterion, finding, or approval-bound value changes
- **WHEN** the digest is recomputed
- **THEN** the affected digest changes
- **AND** a prior seal cannot verify against the new content.

### Requirement: Approval seal contract

The system SHALL define a seal that binds an exact contract digest, validation-result digest, source-snapshot digest, implementation-lineage identity, immutable origin repository/base commit/base tree, optional predecessor-seal digest, approval decision, approver identity, and approval time.

#### Scenario: Approved and unchanged contract verifies

- **GIVEN** a supported seal records approval and all bound digests match
- **WHEN** the verifier evaluates the seal
- **THEN** the result reports a valid recorded approval identity
- **AND** it does not claim semantic or implementation correctness.

#### Scenario: Unapproved or stale material fails closed

- **GIVEN** approval is absent, a bound digest differs, or the schema version is unsupported
- **WHEN** the verifier evaluates the seal
- **THEN** verification is not successful
- **AND** the reason is returned as structured evidence.

#### Scenario: Successor seal attempts to reset the baseline

- **GIVEN** a predecessor seal exists for an active implementation lineage
- **WHEN** a proposed successor changes the origin repository, base commit, or base tree
- **THEN** seal validation fails closed
- **AND** retained implementation work cannot be compared from the later source snapshot alone.

### Requirement: Side-effect-free verifier interface

The system SHALL expose a verifier interface whose result depends only on supplied contract, result, seal, policy, and current source identities.

#### Scenario: Core verifier does not own orchestration

- **GIVEN** a caller requests verification
- **WHEN** the core verifier runs
- **THEN** it performs no network access, project-file writes, rendering, human approval, validator execution, or automatic artifact refinement
- **AND** orchestration remains the caller responsibility.

### Requirement: Explicit assurance limits

The system SHALL describe preflight readiness as structural and provenance assurance rather than proof of design correctness, LLM understanding, or future implementation conformance.

#### Scenario: Consumer presents successful verification

- **GIVEN** a contract and seal verify successfully
- **WHEN** a consumer renders the outcome
- **THEN** it may state that exact reviewed inputs were approved and remain unchanged
- **AND** it SHALL NOT state that the design or implementation is correct solely because verification succeeded.
