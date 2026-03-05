## MODIFIED Requirements

### Requirement: OpenSpec Bridge Adapter Import
The system SHALL import OpenSpec change proposals into SpecFact's project bundle with full backwards compatibility when the `## Intent Trace` section is absent, and include intent context when the section is present.

#### Scenario: Proposal import without Intent Trace section is unchanged
- **GIVEN** an OpenSpec proposal that has no `## Intent Trace` section
- **WHEN** `specfact sync bridge --adapter openspec` is run
- **THEN** the import behaviour is identical to the pre-change behaviour
- **AND** no error, warning, or advisory is emitted related to missing intent trace

#### Scenario: Proposal import includes intent context when section is present
- **GIVEN** an OpenSpec proposal with a valid `## Intent Trace` section
- **WHEN** `specfact sync bridge --adapter openspec` is run (without `--import-intent`)
- **THEN** the proposal's intent trace metadata is attached to the project bundle as read-only context
- **AND** `specfact project health-check` can report that intent context is available for the change

#### Scenario: `openspec validate --strict` validates intent trace when present
- **GIVEN** an OpenSpec change with a proposal containing a `## Intent Trace` section
- **WHEN** `openspec validate <change-id> --strict` is run
- **THEN** the validator checks the YAML block against `intent-trace.schema.json`
- **AND** any schema violations cause a non-zero exit code with descriptive error messages
