## ADDED Requirements

### Requirement: Portable runtime registration is documented at the core handoff

For an installed Code Review bundle exposing portable project runtimes, the core command reference SHALL include the runtime subgroup and project selection options while routing exact runtime semantics to canonical modules documentation.

#### Scenario: Portable runtime commands appear in generated core documentation

- **GIVEN** the reviewed Code Review module exposes runtime inspect and prepare
- **WHEN** core command reference artifacts are generated for that module input
- **THEN** they SHALL include specfact code review runtime inspect and prepare
- **AND** review run SHALL document project-config and project-runtime options
- **AND** the core handoff SHALL link to the modules Code Review guide for configuration, preparation and attachment semantics
