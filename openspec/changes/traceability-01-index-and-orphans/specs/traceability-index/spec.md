## ADDED Requirements

### Requirement: Traceability Index
The system SHALL maintain a queryable index of upstream and downstream links across requirements, architecture, specs, code, and tests.

#### Scenario: Rebuild index captures all artifact layers
- **GIVEN** `specfact trace index --rebuild`
- **WHEN** index generation completes
- **THEN** `.specfact/trace/index.json` contains entries for requirement, architecture, spec, code, and test artifacts
- **AND** each entry contains both upstream and downstream references.

#### Scenario: Orphan command reports missing linkage by type
- **GIVEN** at least one artifact has missing required references
- **WHEN** `specfact trace orphans` runs
- **THEN** output groups orphan findings by artifact type
- **AND** each finding includes artifact identifier and missing link category.

#### Scenario: Matrix export supports machine and human formats
- **GIVEN** a built index
- **WHEN** `specfact trace matrix --format markdown|csv|json` runs
- **THEN** matrix output includes requirement-centered chain rows
- **AND** exported content is deterministic for CI diffs.
