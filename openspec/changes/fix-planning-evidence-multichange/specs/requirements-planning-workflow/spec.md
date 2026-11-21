## ADDED Requirements

### Requirement: Planning-only review evidence selection

The Requirements workflow SHALL validate planning-only sources without selecting implementation approval records. Producer, fresh consumer, and final verifier SHALL preserve source completeness and independently regenerated plan comparison. This boundary SHALL NOT weaken implementation scope, execution, provenance, trusted authority, or promotion verification.

#### Scenario: Multiple planning changes

- **GIVEN** only planning artifacts change across multiple active OpenSpec changes
- **WHEN** the producer, fresh consumer, and final verifier select evidence
- **THEN** implementation review records are not selected and the existing planned validator decides every source's completeness

#### Scenario: Single planning change and unrelated approval

- **GIVEN** a planning-only change has no implementation approval and an unrelated active approval exists
- **WHEN** workflow stages select evidence
- **THEN** neither a missing approval nor the unrelated approval affects planning validation

#### Scenario: Implementation restrictions remain

- **GIVEN** changed paths require implementation evidence
- **WHEN** workflow stages select review evidence
- **THEN** the existing implementation selection is retained and multiple active change scopes remain rejected by the fresh and final verifiers
