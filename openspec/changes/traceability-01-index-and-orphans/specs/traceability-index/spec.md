## ADDED Requirements

### Requirement: Generic Artifact Evidence Index

The system SHALL build a deterministic, serializable index of normalized
artifact records and links. Core SHALL not own collection, filesystem
persistence, or command rendering.

#### Scenario: Requirements-only input does not require architecture

- **GIVEN** normalized requirements with downstream evidence links
- **WHEN** they are mapped into the generic index without architecture records
- **THEN** no architecture finding is emitted solely because architecture is absent.

#### Scenario: Index classifies deterministic evidence findings

- **GIVEN** normalized records containing an unlinked artifact, a dangling link,
  a duplicate identity, or a self-contradicting link
- **WHEN** the index is built
- **THEN** it emits bounded orphan, drift, ambiguity, and contradiction findings
  in stable order.

#### Scenario: Rebuild reports changed and removed identities

- **GIVEN** a prior index and an updated record set
- **WHEN** the core index rebuilds
- **THEN** its result identifies changed and removed artifact identities without
  writing generated state.
