# multi-location-discovery Specification

## Purpose
TBD - created by archiving change marketplace-01-central-module-registry. Update Purpose after archive.
## Requirements
### Requirement: Discover modules from multiple paths

The system SHALL discover modules from built-in, marketplace, and custom paths in priority order.

#### Scenario: Discovery scans all three locations
- **WHEN** module discovery runs
- **THEN** system SHALL scan {site-packages}/specfact_cli/modules/
- **AND** SHALL scan ~/.specfact/marketplace-modules/ if exists
- **AND** SHALL scan ~/.specfact/custom-modules/ if exists

#### Scenario: Built-in modules take priority
- **WHEN** module "backlog" exists in both built-in and marketplace
- **THEN** system SHALL use built-in version
- **AND** SHALL log warning about shadowed marketplace module

#### Scenario: Marketplace modules discovered when no built-in
- **WHEN** module exists in marketplace but not built-in
- **THEN** system SHALL discover and register marketplace module

### Requirement: Source tracking for discovered modules

The system SHALL track the source (built-in/marketplace/custom) for each discovered module.

#### Scenario: Module metadata includes source
- **WHEN** module is discovered
- **THEN** system SHALL record source in module metadata
- **AND** source SHALL be one of: "builtin", "marketplace", "custom"

#### Scenario: List command shows module source
- **WHEN** user runs `specfact module list`
- **THEN** each module SHALL display source indicator
- **AND** built-in modules SHALL be marked as "[built-in]"

### Requirement: Graceful handling of missing paths

The system SHALL handle missing marketplace or custom paths without errors.

#### Scenario: Marketplace path does not exist
- **WHEN** ~/.specfact/marketplace-modules/ does not exist
- **THEN** discovery SHALL continue with built-in modules only
- **AND** SHALL NOT log warning (normal state)

#### Scenario: Custom path does not exist
- **WHEN** ~/.specfact/custom-modules/ does not exist
- **THEN** discovery SHALL continue normally
- **AND** SHALL NOT raise exception

