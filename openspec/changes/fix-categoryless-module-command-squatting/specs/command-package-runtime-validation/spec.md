## ADDED Requirements

### Requirement: Category Grouping Prevents Root Command Squatting

When category grouping is enabled, the system SHALL register package commands only through an explicit module category and SHALL NOT register category-less package commands at the CLI root.

#### Scenario: Category-less workspace module cannot claim a root command

- **GIVEN** category grouping is enabled
- **AND** a discovered workspace module omits its category and declares a removed flat command name
- **WHEN** module package commands are registered
- **THEN** the declared command SHALL NOT be added to the root command registry
- **AND** the package loader SHALL NOT execute through that command

#### Scenario: Explicit legacy mode retains flat registration

- **GIVEN** category grouping is explicitly disabled
- **AND** a discovered module omits its category
- **WHEN** module package commands are registered
- **THEN** the declared command SHALL retain legacy root registration behavior
