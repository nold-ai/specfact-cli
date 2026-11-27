## ADDED Requirements

### Requirement: Authenticate unchanged inherited proof before planning selection

Producer, independent execution and final verdict SHALL authenticate the same live native ancestry.
A planning child MAY select its stack root head as a proposal diff boundary only when every changed path
is a regular non-executable OpenSpec planning document or sidecar, and no source directory covered by
the root's changed OpenSpec sources is modified. All root runtime, selected tests, test support, mappings
and delivery bytes SHALL remain unchanged. Protected dev/main SHALL remain the trusted validator source.
The root proof workflow and its local CI actions SHALL match protected-base Git objects; a root that changes
those controls SHALL retain the complete proof path. The system SHALL authenticate successful exact-root
Requirements and member-authority runs from their
expected GitHub Actions app, repository, workflow IDs, paths, event, branch and SHA, plus root signature.

#### Scenario: Closed planning layer preserves both maturities

- **GIVEN** a live native child containing only eligible planning changes above an unchanged verified root
- **WHEN** its current-root Requirements and authority checks and signed head authenticate successfully
- **THEN** planning selection SHALL use that root head for every post-root proposal source
- **AND** protected-base trust and the root's complete verified implementation proof SHALL remain unchanged
- **AND** child proposals SHALL report planned maturity without implementation or RED claims

#### Scenario: Runtime or inherited source change retains full proof

- **GIVEN** a child changes code, tests, workflows, delivery, canonical specs or root-covered source files
- **WHEN** its boundary is resolved
- **THEN** it SHALL NOT receive a planning boundary
- **AND** the existing full-stack implementation and exact mapping/plan/RED checks SHALL remain mandatory

#### Scenario: Forged or stale upstream proof is rejected

- **GIVEN** eligible planning paths but missing, failed, pending, unsigned, foreign or mismatched root proof
- **WHEN** the boundary is resolved
- **THEN** resolution SHALL fail before proposal evidence is consumed
- **AND** no stack membership or child grant SHALL substitute for inherited proof

#### Scenario: Symlink or executable document is not planning

- **GIVEN** a child supplies an executable, symlink or non-document payload under an OpenSpec path
- **WHEN** the boundary is resolved
- **THEN** it SHALL NOT receive a planning boundary
- **AND** root-covered document deletions or moves SHALL NOT escape source protection

### Requirement: Reconcile planning evidence independently of verifier trust

All three Requirements stages SHALL derive the same authenticated planning selection and context digest.
They SHALL continue materializing validator, runtime fixtures and delivery controls from protected-base
objects. Final planning plan equality SHALL remain enforced independently of the inherited root verdict.

#### Scenario: Every consumer retains protected validator materialization

- **GIVEN** an eligible authenticated planning child
- **WHEN** producer, independent execution and final verdict select its post-root proposals
- **THEN** all three SHALL use the same planning diff boundary
- **AND** protected validator materialization and complete plan/context equality SHALL remain enforced
