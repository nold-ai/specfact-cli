## ADDED Requirements

### Requirement: Intent Trace Section Schema
The system SHALL define a JSON Schema at `openspec/schemas/intent-trace.schema.json` that validates the `## Intent Trace` YAML block in OpenSpec proposal files.

#### Scenario: Valid intent trace section passes schema validation
- **GIVEN** an OpenSpec proposal with a correctly structured `## Intent Trace` YAML block
- **WHEN** `openspec validate <change-id> --strict` is run
- **THEN** the intent trace section validates without errors
- **AND** the validation output confirms intent trace section is present and valid

#### Scenario: Invalid intent trace section fails schema validation
- **GIVEN** an OpenSpec proposal with a `## Intent Trace` YAML block missing a required field (e.g., `id` on a `BusinessOutcome`)
- **WHEN** `openspec validate <change-id> --strict` is run
- **THEN** the validation exits with a non-zero code
- **AND** the error message identifies the specific field violation and the line context

#### Scenario: Missing intent trace section is valid (section is optional)
- **GIVEN** an OpenSpec proposal without any `## Intent Trace` section
- **WHEN** `openspec validate <change-id> --strict` is run
- **THEN** the validation passes without intent-trace errors
- **AND** no warning about missing intent trace is emitted in normal mode

#### Scenario: Intent trace schema includes schema version field
- **GIVEN** an intent trace YAML block with `schema_version: "1.0"`
- **WHEN** the bridge adapter reads the block
- **THEN** it accepts the artifact and records the schema version
- **AND** if the schema version is unknown the adapter emits a clear error with supported versions

### Requirement: Intent Trace Evidence Field in Archive
The system SHALL support an optional `evidence` field in change archive metadata pointing to the evidence JSON envelope file produced during implementation.

#### Scenario: Archive metadata includes evidence reference
- **GIVEN** an archived change that generated a governance evidence artifact
- **WHEN** the archive metadata is read
- **THEN** the `evidence` field contains a relative path to the `.specfact/evidence/` JSON file
- **AND** the path resolves to a readable file on disk

#### Scenario: Archive without evidence field is valid
- **GIVEN** an archived change that did not produce governance evidence
- **WHEN** the archive metadata is validated
- **THEN** validation passes without errors related to the missing evidence field
