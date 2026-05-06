## MODIFIED Requirements

### Requirement: Telemetry Emitter Uses a PII-Safe Payload Contract

The telemetry emitter SHALL allow redacted operational metadata, including FinOps session metrics, while continuing to reject prompt content, repository content, and other free-form sensitive strings.

#### Scenario: Safe FinOps metadata is allowed

- **GIVEN** a CLI invocation has token counts, cost metadata, and an outcome enum available
- **WHEN** the telemetry emitter builds its payload
- **THEN** those FinOps fields are included if they satisfy the allowlist contract
- **AND** prompt text, spec text, and repository paths remain excluded.

#### Scenario: Unsupported free-form FinOps fields are rejected

- **GIVEN** an emitter extension attempts to add prompt excerpts or unbounded notes to the FinOps payload
- **WHEN** payload validation runs
- **THEN** the emitter rejects those fields before transmission
- **AND** the local audit log reflects only the redacted, allowed payload.
