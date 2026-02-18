## MODIFIED Requirements

### Requirement: Apply locally with preflight

The system SHALL provide `specfact patch apply <patchfile>` that applies the patch locally with a preflight check; user confirmation or explicit flag required.

#### Scenario: Local apply performs real patch operation

- **GIVEN** a valid unified diff patch file
- **WHEN** the user runs `specfact patch apply <patchfile>`
- **THEN** preflight validation runs before apply
- **AND** the patch is actually applied to local target files (not a stub success path)
- **AND** command exits non-zero on patch apply failure.

### Requirement: Write upstream with explicit confirmation

The system SHALL provide `specfact patch apply --write` (or equivalent) that updates upstream (GitHub/ADO) only with explicit user confirmation; idempotent for posted comments/updates (no duplicates).

#### Scenario: Write orchestration is explicit, confirmed, and idempotent

- **GIVEN** upstream write mode is requested
- **WHEN** the user runs `specfact patch apply <patchfile> --write --yes`
- **THEN** upstream write path executes only after confirmation
- **AND** repeated invocation with the same operation key does not create duplicate writes/comments
- **AND** failures in write orchestration surface clear non-zero error outcomes.
