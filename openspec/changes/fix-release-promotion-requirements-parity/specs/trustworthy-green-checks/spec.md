## ADDED Requirements

### Requirement: Exact release promotion reuses protected development evidence

The Requirements workflow SHALL recognize a release promotion only when a
GitHub pull-request event identifies the same repository as both base and head,
the base ref is exactly `main`, the head ref is exactly `dev`, every Requirements
stage is checked out at the event's exact head commit, live `main` and `dev` tips
equal the event commits, and `main` is an ancestor of `dev`. The workflow SHALL
first authenticate the candidate tree with an immutable centrally pinned
authority validator, then require both deterministic aggregate planning
validation and a distinct authenticated `promotion-reused` attestation instead
of one synthetic review acceptance for the accumulated active OpenSpec changes.

#### Scenario: Exact protected development promotion is accepted

- **GIVEN** a pull request whose base and head repository identities equal the
  event repository
- **AND** the exact refs are `main` and `dev`
- **AND** the event commits equal the checked-out and live remote tips and
  `main` is an ancestor of `dev`
- **AND** the current head has a live, expiring, unedited member authority
  accepted by the exact pinned central validator bytes
- **WHEN** the accumulated branch delta contains multiple active OpenSpec
  changes
- **THEN** each stage SHALL validate the deterministic aggregate plan and the
  canonical `promotion-reused` attestation
- **AND** SHALL NOT require a fabricated aggregate review-evidence record.

### Requirement: Lookalike promotions retain ordinary proof requirements

Every pull request that does not satisfy the complete protected-promotion
identity SHALL retain the existing single-change maturity and proof requirements.

#### Scenario: Lookalike promotion remains fail closed

- **GIVEN** a pull request from a fork, another repository identity, another
  base, or a branch merely named similarly to `dev`
- **WHEN** the Requirements workflow classifies the pull request
- **THEN** it SHALL NOT use the release-promotion path
- **AND** the existing changed-path maturity, single-change acceptance, proof,
  and artifact rules SHALL remain enforced.

### Requirement: Promotion reuse authenticates complete prior provenance

The workflow SHALL authenticate its current candidate tree with exact pinned
central authority bytes, then authenticate the unique merged pull request that
produced the exact current `dev` tree, that pull request's successful
GitHub-Actions Requirements and external-authority runs, and the Requirements
run's exact unexpired, digest-bound producer and fresh-execution artifacts.

#### Scenario: Promotion provenance is incomplete or stale

- **GIVEN** an otherwise exact same-repository `dev` to `main` event
- **WHEN** any commit, tree, live tip, ancestry, source pull request, check run,
  workflow, application, artifact identity, expiry, digest, report, plan, or
  JUnit binding is absent, ambiguous, stale, unsuccessful, or mismatched, or
  the central validator commit/tree/blob/digest or member authority is invalid
- **THEN** that stage SHALL fail closed before accepting promotion reuse.

### Requirement: Promotion stages independently validate reuse

Producer, fresh execution, and final verification SHALL each fetch and validate
the live source evidence and SHALL agree on one canonical promotion attestation.
Trusted core, retained-RED ancestry, Code Review, and release gates SHALL remain
`main`-relative. For the exact legacy `main` base
`b1e517e60e669eaba15a18ecfa83ef5a9df65276` only, a trusted-core materializer
MAY obtain only the two absent frozen Code Review inputs from source commit
`3ea3d9b4492ade6ec5683fac83c5b5090b0cb547` after authenticating tree
`4d61f0420952b5c3913aa7c771a154c2913a9e14`, input blob
`6f0f16ba49e10d6b4f4132c112e3b4c5855e850f`, lock blob
`bf0033c19cada1b656beb818e43366828ce6fabb`, and
base-to-source-to-candidate ancestry. Any other missing, mixed, changed, or
unrelated source state SHALL fail closed. The exception SHALL not apply when the
base contains both inputs.

#### Scenario: Promotion stages independently agree

- **GIVEN** the producer emitted a canonical `promotion-reused` attestation
- **WHEN** the fresh consumer and final verifier evaluate the promotion
- **THEN** each SHALL independently fetch and validate the live source evidence
- **AND** SHALL require its canonical attestation bytes to equal the prior-stage
  attestation
- **AND** trusted core, retained-RED ancestry, Code Review, and release gates
  SHALL remain `main`-relative except for the exact, ancestry-bound legacy
  two-input bootstrap defined above.
