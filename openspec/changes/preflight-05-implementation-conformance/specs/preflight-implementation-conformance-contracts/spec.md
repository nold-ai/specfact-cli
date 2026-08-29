## ADDED Requirements

### Requirement: Versioned implementation snapshot

The system SHALL define a versioned implementation snapshot whose kind is `worktree`, `index`, or `range` and which contains repository identity, exact kind-specific Git identity, complete changed-path manifest, public-interface records, test/evidence references, and producer, policy, toolchain, and extractor identities.

The `worktree` kind SHALL bind a full base commit ID and worktree-manifest digest and include staged, unstaged, and untracked state relative to that base. The `index` kind SHALL bind a full base commit ID and exact index tree ID and exclude untracked paths unless staged as additions. The `range` kind SHALL bind full base/head commit IDs and base/head tree IDs and SHALL NOT represent untracked paths. Every snapshot base SHALL equal the seal-bound implementation-lineage origin repository/base commit/base tree, including after refinement or reapproval. A range head SHALL be proven to descend from that origin by a producer/policy/toolchain-bound ancestry attestation, and its manifest SHALL cover the complete lineage-origin-to-head range. Every kind SHALL preserve additions, deletions, both rename endpoints, before/after modes, symlink target identity, and byte-preserving path identity where those states exist. Rename interpretation SHALL be bound to producer, policy, and toolchain identity.

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

#### Scenario: Final range truncates the sealed baseline

- **GIVEN** a range snapshot starts from a commit or tree other than the seal-bound implementation-lineage origin baseline, or its head ancestry from that origin is absent or invalid
- **WHEN** the snapshot is validated for final conformance
- **THEN** the baseline mismatch is `stale` or the unresolved ancestry is `unverifiable`, and the result is `UNKNOWN`
- **AND** no current-seal or caller-selected shorter range can omit implementation retained from an earlier seal and pass.

### Requirement: Sealed obligation mapping

The system SHALL map approved scope roles, component ownership, interfaces, acceptance criteria, risk rows, Requirements-plan references, test intent, verification stages, and exclusions from one valid preflight seal to normalized implementation evidence. A checkpoint MAY carry the deterministic affected subset for its sealed stage/profile. A final range result SHALL bind the obligation-map digest and SHALL require the exhaustive transitive closure for every changed governed path/interface and every applicable sealed component, acceptance criterion, risk row, Requirements case, component target, stage including `ci`, and exclusion. Every evidence record SHALL carry a producer authority class and verifiable provenance bound to its exact snapshot or range. An obligation whose earliest stage is `ci` SHALL be satisfiable only by evidence from a seal/policy-authorized protected-CI producer with authenticated provenance bound to the exact immutable range; local or caller-asserted producer identity SHALL NOT satisfy it.

#### Scenario: Approved acceptance criterion has no evidence

- **GIVEN** a sealed acceptance criterion requires observable proof
- **WHEN** no matching test or evidence record is supplied
- **THEN** conformance includes a missing or unverifiable finding
- **AND** the criterion is not inferred satisfied from an overall test exit code.

#### Scenario: Final range obligation map is incomplete

- **GIVEN** an immutable range affects one or more sealed obligations
- **WHEN** its final obligation map omits, duplicates, cannot deterministically resolve, or selects no member of the exhaustive applicable closure
- **THEN** the verifier returns an `unverifiable` finding and `UNKNOWN`
- **AND** final conformance cannot pass by supplying a smaller obligation map.

#### Scenario: CI-stage evidence lacks protected provenance

- **GIVEN** an exhaustive final range map contains an applicable obligation whose earliest verification stage is `ci`
- **WHEN** evidence is absent, locally produced, caller-asserted, unauthenticated, or bound to a different range
- **THEN** the verifier returns an `unverifiable` finding and `UNKNOWN`
- **AND** final conformance cannot pass until authorized protected-CI evidence for the exact range is supplied.

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

The system SHALL define an `ImplementationConformanceResult` that accepts only an explicit immutable range identity containing repository identity, full base and head commit IDs, and base and head tree identities. Its complete path manifest and tree attestations SHALL bind to that exact repository and base/head range.

#### Scenario: Worktree evidence is supplied as final conformance

- **GIVEN** only worktree or index evidence is available
- **WHEN** final conformance is requested
- **THEN** result construction is unsuccessful
- **AND** the missing immutable range identity is reported.

### Requirement: Closed implementation assurance finding classes

Checkpoint and conformance results SHALL distinguish mutually exclusive `missing`, `unexpected`, `modified`, `violated`, `stale`, and `unverifiable` findings with stable source and evidence identities. Classification precedence SHALL be `stale`, `unverifiable`, `unexpected`, `missing`, `modified`, then `violated`: stale identifies changed seal-bound inputs; unverifiable identifies absent, ambiguous, unsupported, or unreconciled required identity/evidence; unexpected identifies implementation without a sealed mapping; missing identifies a sealed required counterpart with no implementation/evidence; modified identifies a counterpart whose structural identity differs; violated identifies reconciled identities and executed evidence whose semantic observable differs from the sealed expectation.

`stale` and `unverifiable` SHALL be blocking uncertainty, `unexpected` SHALL be blocking failure, and required `missing`, `modified`, and `violated` SHALL be blocking failure. Only sealed policy that already marks an obligation non-required may make `missing`, `modified`, or `violated` advisory. Aggregation SHALL return `FAIL` when any determinate blocking failure exists, otherwise `UNKNOWN` when blocking uncertainty exists, otherwise `PASS`. Caller-owned applicability MAY construct `NOT_APPLICABLE`; the verifier SHALL NOT infer it.

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

#### Scenario: Reconciled semantic evidence violates an observable

- **GIVEN** a governed implementation path and its evidence reconcile to stable sealed scope, requirement, risk-case, selector, producer, and current-run evidence identities
- **AND** the implementation counterpart is present and its structural identity matches the sealed expectation
- **WHEN** the executed evidence reports an observed semantic outcome different from the sealed acceptance or risk-case observable
- **THEN** the finding is `violated`, not `unexpected`, `missing`, or `modified`
- **AND** it carries the stable sealed source identity and current implementation/evidence identities.

### Requirement: Side-effect-free implementation assurance verifier

The core verifier SHALL accept the upstream design contract, validation result, seal, policy, and current source identities plus supplied sealed obligations and implementation evidence. It SHALL verify the upstream inputs before comparing obligations and SHALL execute no code, tests, extractors, network calls, persistence, rendering, applicability policy, or automatic contract edits.

#### Scenario: Caller requests comparison

- **GIVEN** a design contract, validation result, seal, policy, current source identities, and normalized implementation snapshot
- **WHEN** the core conformance verifier runs
- **THEN** it rejects stale or mismatched upstream identities before obligation comparison and otherwise returns deterministic findings and limits for those inputs
- **AND** all evidence collection and policy orchestration remain caller-owned.

### Requirement: Explicit implementation assurance limits

The system SHALL describe a successful result as conformance to captured obligations and evidence, not proof of complete runtime behavior, hidden-side-effect absence, security, or design quality.

#### Scenario: Consumer renders a successful comparison

- **GIVEN** every required mapped obligation has accepted evidence and no blocking drift remains
- **WHEN** a consumer presents the result
- **THEN** it identifies the sealed contract, implementation snapshot, extractors, evidence, and policy used
- **AND** it includes the declared assurance limits and exact local or range authority.
