## ADDED Requirements

### Requirement: Versioned implementation snapshot

The system SHALL define a versioned implementation snapshot whose kind is `worktree`, `index`, or `range` and which contains the exact base plus kind-specific identity, complete changed-path manifest, public-interface records, test/evidence references, and producer, policy, toolchain, and extractor identities.

#### Scenario: Snapshot preserves complete Git path semantics

- **GIVEN** an implementation adds, deletes, renames, changes mode, symlinks, or introduces an untracked path supported by its snapshot kind
- **WHEN** the snapshot is normalized
- **THEN** the complete transition, including both rename endpoints, is retained
- **AND** quoted, Unicode, and trailing-character paths are not collapsed or silently omitted.

#### Scenario: Snapshot evidence lacks identity

- **GIVEN** an implementation artifact or test result has no stable revision, digest, or producer identity
- **WHEN** the snapshot is normalized
- **THEN** that evidence is marked unverifiable
- **AND** it cannot satisfy a sealed-contract obligation.

### Requirement: Sealed obligation mapping

The system SHALL map approved scope roles, component ownership, interfaces, acceptance criteria, risk rows, Requirements-plan references, test intent, verification stages, and exclusions from one valid preflight seal to normalized implementation evidence.

#### Scenario: Approved acceptance criterion has no evidence

- **GIVEN** a sealed acceptance criterion requires observable proof
- **WHEN** no matching test or evidence record is supplied
- **THEN** conformance includes a missing or unverifiable finding
- **AND** the criterion is not inferred satisfied from an overall test exit code.

### Requirement: Separate local checkpoint result

The system SHALL define a `DevelopmentCheckpointResult` with `PASS`, `FAIL`, `UNKNOWN`, or `NOT_APPLICABLE` status and authority limited to `local_worktree` or `local_index`.

#### Scenario: Local result cannot become PR authority

- **GIVEN** a worktree or index checkpoint passes
- **WHEN** a consumer attempts to label or promote it as range or protected pull-request evidence
- **THEN** result validation rejects the authority claim
- **AND** a new immutable-range evaluation remains required.

#### Scenario: Required local evidence is unresolved

- **GIVEN** a matching seal exists but scope, component ownership, selector, runner, or required evidence is ambiguous or unavailable
- **WHEN** checkpoint status is aggregated
- **THEN** the result is `UNKNOWN`
- **AND** it is not converted to `PASS` or `NOT_APPLICABLE`.

### Requirement: Immutable implementation conformance result

The system SHALL define an `ImplementationConformanceResult` that accepts only an explicit immutable base/head range identity.

#### Scenario: Worktree evidence is supplied as final conformance

- **GIVEN** only worktree or index evidence is available
- **WHEN** final conformance is requested
- **THEN** result construction is unsuccessful
- **AND** the missing immutable range identity is reported.

### Requirement: Closed implementation assurance finding classes

Checkpoint and conformance results SHALL distinguish missing, unexpected, modified, violated, stale, and unverifiable findings with stable source and evidence identities.

#### Scenario: Implementation adds work outside approved scope

- **GIVEN** a changed public interface or governed path has no approved scope mapping and is not an accepted generated/excluded artifact
- **WHEN** conformance is evaluated
- **THEN** an unexpected finding identifies the implementation evidence and nearest contract boundary
- **AND** policy determines whether reapproval is required.

#### Scenario: Sealed contract changed after approval

- **GIVEN** the current contract digest differs from the approved seal
- **WHEN** conformance is evaluated
- **THEN** the result is stale
- **AND** comparison cannot pass until a new preflight review and approval exist.

### Requirement: Side-effect-free implementation assurance verifier

The core verifier SHALL compare supplied sealed obligations and implementation evidence without executing code, tests, extractors, network calls, persistence, rendering, or automatic contract edits.

#### Scenario: Caller requests comparison

- **GIVEN** a valid seal and normalized implementation snapshot
- **WHEN** the core conformance verifier runs
- **THEN** it returns deterministic findings and limits for those inputs
- **AND** all evidence collection and policy orchestration remain caller-owned.

### Requirement: Explicit implementation assurance limits

The system SHALL describe a successful result as conformance to captured obligations and evidence, not proof of complete runtime behavior, hidden-side-effect absence, security, or design quality.

#### Scenario: Consumer renders a successful comparison

- **GIVEN** every required mapped obligation has accepted evidence and no blocking drift remains
- **WHEN** a consumer presents the result
- **THEN** it identifies the sealed contract, implementation snapshot, extractors, evidence, and policy used
- **AND** it includes the declared assurance limits and exact local or range authority.
