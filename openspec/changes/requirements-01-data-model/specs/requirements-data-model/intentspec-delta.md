## ADDED Requirements

### Requirement: IntentSpec Schema Compatibility
The system SHALL ensure `BusinessOutcome` and `BusinessRule` schemas are compatible with the IntentSpec.org JSON Schema standard (5 fields: Objective, User Goal, Outcomes, Edge Cases, Verification), so that IntentSpec-formatted intent documents can be imported without data loss.

#### Scenario: BusinessOutcome maps to all 5 IntentSpec fields
- **GIVEN** an IntentSpec-formatted YAML document with fields: objective, user_goal, outcomes, edge_cases, verification
- **WHEN** it is imported via `specfact requirements capture --format intentspec`
- **THEN** the resulting `BusinessOutcome` record preserves all 5 IntentSpec fields in the stored artifact
- **AND** the imported artifact validates against the `BusinessOutcome` Pydantic schema without errors

#### Scenario: SQUER 7-question answers map to IntentSpec fields
- **GIVEN** a completed SQUER intent interview with 7 answers
- **WHEN** the interview output is serialized to a `BusinessOutcome` artifact
- **THEN** the serialization produces all 5 IntentSpec fields as a superset (SQUER answers cover objective, user_goal, outcomes, edge_cases, and verification)
- **AND** no data is silently dropped from the SQUER answers during the mapping

### Requirement: Traceability Invariants
The system SHALL enforce three traceability invariants as preconditions on the publish gate for requirement artifacts:

1. **Traceability invariant**: Every shipped feature SHALL trace backward to at least one `BusinessOutcome` and forward through `BusinessRule` (G/W/T), `ArchitecturalConstraint`, specs, contracts, and tests.
2. **Evidence completeness invariant**: No artifact SHALL pass the publish gate without a corresponding evidence record capturing validation timestamp, tool version, verdict (pass/fail/error), and artifact hash.
3. **Intent schema conformance invariant**: `BusinessOutcome`, `BusinessRule`, and `ArchitecturalConstraint` documents SHALL validate against their canonical schemas before entering the pipeline.

#### Scenario: Traceability invariant enforced on publish gate
- **GIVEN** a `BusinessOutcome` with no downstream spec reference
- **WHEN** `specfact enforce stage --preset strict` runs the publish gate
- **THEN** the gate blocks with a BLOCK verdict
- **AND** the blocking reason identifies the orphaned `BusinessOutcome` ID and the missing spec link

#### Scenario: Intent schema conformance checked before pipeline entry
- **GIVEN** a `BusinessRule` YAML file with a missing `given` field
- **WHEN** `specfact requirements validate` is run
- **THEN** the command exits non-zero
- **AND** the error output identifies the missing field, its expected type, and the file path
