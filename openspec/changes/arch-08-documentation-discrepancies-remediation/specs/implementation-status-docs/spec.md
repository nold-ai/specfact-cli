# implementation-status-docs Specification

A single, maintained place describes what is implemented versus planned and points to OpenSpec changes for planned features.

## ADDED Requirements

### Requirement: Implemented vs planned clearly stated

The implementation status documentation SHALL clearly mark each feature (e.g. architecture commands, protocol FSM, change tracking) as implemented or planned, with brief notes on scope where relevant.

#### Scenario: Reader checks feature status
- **GIVEN** the implementation status documentation (e.g. docs/architecture/implementation-status.md)
- **WHEN** a reader checks the status of a feature
- **THEN** each feature is clearly marked as implemented or planned
- **AND** scope notes are provided (e.g. change tracking: models exist, limited adapter support)

### Requirement: Pointers to OpenSpec for planned features

For planned or partially implemented features, the implementation status doc SHALL link or reference the relevant OpenSpec change (e.g. architecture-01-solution-layer for architecture derive/validate/trace).

#### Scenario: Reader finds spec for planned feature
- **GIVEN** a planned or partially implemented feature
- **WHEN** the implementation status doc describes it
- **THEN** it links or references the relevant OpenSpec change
- **AND** readers can find the spec and roadmap

### Requirement: Current limitations documented

Current limitations for change tracking and protocol/FSM behavior SHALL be stated (e.g. no FSM engine, partial adapter support for change tracking) so that expectations match reality.

#### Scenario: Reader checks limitations
- **GIVEN** change tracking and protocol/FSM behavior
- **WHEN** a user or contributor reads the implementation status
- **THEN** current limitations are stated
- **AND** expectations align with implementation

### Requirement: Implementation status discoverable

The implementation status page SHALL be linked from the architecture README or reference architecture page so it can be found without searching.

#### Scenario: User navigates architecture docs
- **GIVEN** the docs site
- **WHEN** a user navigates architecture docs
- **THEN** the implementation status page is linked
- **AND** discoverable from the architecture index or README
