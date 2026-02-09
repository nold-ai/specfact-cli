# module-packages Delta Specification

## ADDED Requirements

### Requirement: Module discovery supports multiple source locations

The system SHALL extend module discovery to scan built-in, marketplace, and custom paths with source tracking.

#### Scenario: Discovery function returns source information
- **WHEN** discover_package_metadata() finds a module
- **THEN** it SHALL include source field in metadata
- **AND** source SHALL be "builtin", "marketplace", or "custom"

#### Scenario: Registry stores module source
- **WHEN** module is registered
- **THEN** registry SHALL persist source information
- **AND** SHALL be queryable via module list command
