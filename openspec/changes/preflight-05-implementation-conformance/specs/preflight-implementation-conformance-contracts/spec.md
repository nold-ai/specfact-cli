## ADDED Requirements

### Requirement: Versioned implementation snapshot

The system SHALL define a versioned implementation snapshot containing exact repository revisions, changed-path manifest, public-interface records, test/evidence references, and extractor identities.

#### Scenario: Snapshot evidence lacks identity

- **GIVEN** an implementation artifact or test result has no stable revision, digest, or producer identity
- **WHEN** the snapshot is normalized
- **THEN** that evidence is marked unverifiable
- **AND** it cannot satisfy a sealed-contract obligation.

### Requirement: Sealed obligation mapping

The system SHALL map approved scope, interface, acceptance, test-intent, and exclusion obligations from one valid preflight seal to normalized implementation evidence.

#### Scenario: Approved acceptance criterion has no evidence

- **GIVEN** a sealed acceptance criterion requires observable proof
- **WHEN** no matching test or evidence record is supplied
- **THEN** conformance includes a missing or unverifiable finding
- **AND** the criterion is not inferred satisfied from an overall test exit code.

### Requirement: Closed conformance drift classes

The conformance result SHALL distinguish missing, unexpected, modified, stale, and unverifiable findings with stable source and evidence identities.

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

### Requirement: Side-effect-free conformance verifier

The core verifier SHALL compare supplied sealed obligations and implementation evidence without executing code, tests, extractors, network calls, persistence, rendering, or automatic contract edits.

#### Scenario: Caller requests comparison

- **GIVEN** a valid seal and normalized implementation snapshot
- **WHEN** the core conformance verifier runs
- **THEN** it returns deterministic findings and limits for those inputs
- **AND** all evidence collection and policy orchestration remain caller-owned.

### Requirement: Explicit conformance limits

The system SHALL describe a successful result as conformance to captured obligations and evidence, not proof of complete runtime behavior, hidden-side-effect absence, security, or design quality.

#### Scenario: Consumer renders a successful comparison

- **GIVEN** every required mapped obligation has accepted evidence and no blocking drift remains
- **WHEN** a consumer presents the result
- **THEN** it identifies the sealed contract, implementation snapshot, extractors, evidence, and policy used
- **AND** it includes the declared assurance limits.
