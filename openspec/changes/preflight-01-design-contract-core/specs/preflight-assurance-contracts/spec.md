## ADDED Requirements

### Requirement: Normalized preflight design contract

The system SHALL define a versioned preflight design contract that records the exact reviewed change identity, source identities, scope, exclusions, assumptions, unknowns, dependencies, interfaces, acceptance criteria, test intent, risks, rollback intent, and approval policy.

#### Scenario: Contract preserves source and scope identity

- **GIVEN** a change assembled from OpenSpec, repository governance, GitHub metadata, and repository state
- **WHEN** the design contract is normalized
- **THEN** every input is represented by a stable source kind, location, revision or digest, and loader identity
- **AND** in-scope and explicitly excluded work are distinct contract fields.

#### Scenario: Unknown information is not silently resolved

- **GIVEN** a dependency, interface, or acceptance criterion cannot be verified
- **WHEN** the contract is created
- **THEN** the uncertainty is recorded as an explicit unknown
- **AND** it is not converted into an assumption or successful validation result.

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

- **GIVEN** a source identity, scope boundary, acceptance criterion, finding, or approval-bound value changes
- **WHEN** the digest is recomputed
- **THEN** the affected digest changes
- **AND** a prior seal cannot verify against the new content.

### Requirement: Approval seal contract

The system SHALL define a seal that binds an exact contract digest, validation-result digest, source-snapshot digest, approval decision, approver identity, and approval time.

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
