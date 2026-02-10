# Spec: Module Lifecycle Management

## ADDED Requirements

### Requirement: Lifecycle registration loads module-declared bridges

The system SHALL load and register module-declared service bridges during module lifecycle registration.

#### Scenario: Registration wires declared bridge converters

- **WHEN** `register_module_package_commands()` processes an enabled module with valid `service_bridges`
- **THEN** each declared converter SHALL be registered into `BridgeRegistry`
- **AND** registration SHALL occur without direct core imports from module command internals.

#### Scenario: Bridge registration respects module enable/disable state

- **WHEN** a module is disabled or skipped due to compatibility/dependency failure
- **THEN** its bridge declarations SHALL NOT be registered.

### Requirement: Lifecycle handles bridge conflicts deterministically

The system SHALL handle duplicate bridge IDs predictably and with actionable diagnostics.

#### Scenario: Duplicate bridge ID detected

- **WHEN** two enabled modules declare the same bridge ID
- **THEN** lifecycle registration SHALL apply deterministic conflict handling
- **AND** SHALL log warning/debug details identifying both modules and bridge ID.

### Requirement: Bridge registration failures do not block unrelated modules

The system SHALL degrade gracefully when individual bridge declarations fail.

#### Scenario: Converter import failure is non-fatal

- **WHEN** a module declares a converter class that cannot be imported
- **THEN** lifecycle registration SHALL skip that bridge declaration
- **AND** continue registering other valid modules and bridges.

### Requirement: Lifecycle protocol reporting is accurate and non-duplicative

The system SHALL report ModuleIOContract compliance based on actual module capabilities and avoid duplicate warning emission.

#### Scenario: Compliant module is not misreported as legacy

- **WHEN** lifecycle registration inspects an enabled module that exposes required ModuleIOContract operations
- **THEN** compliance reporting SHALL classify it as full or partial support
- **AND** SHALL NOT classify it as legacy due to inspection-path mismatch.

#### Scenario: Warning output is emitted once per condition

- **WHEN** lifecycle registration logs protocol warnings during startup
- **THEN** each warning condition SHALL be emitted once per module/event
- **AND** a single summary line SHALL report aggregate full/partial/legacy counts.
