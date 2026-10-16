## MODIFIED Requirements

### Requirement: `category_grouping_enabled` config flag controls grouping behaviour

The system SHALL read the grouping flag from operator environment or user configuration. Categorized
installed bundles SHALL retain category routing in either mode, preserving the shipped removal of flat
bundle shims. The flag SHALL control only the compatibility permission for category-less project packages;
permanent core and official category root reservations SHALL remain enforced in both modes.

#### Scenario: Grouping enabled by default

- **GIVEN** no explicit grouping flag
- **WHEN** the CLI initializes
- **THEN** grouped mode SHALL default to true
- **AND** category-less project packages SHALL be rejected

#### Scenario: Grouping disabled via config

- **GIVEN** the operator explicitly disables grouping
- **WHEN** the CLI initializes
- **THEN** categorized installed bundles SHALL retain category routing without flat bundle shims
- **AND** category-less project packages MAY register only unreserved legacy root commands
- **AND** permanent core and official category roots SHALL remain reserved

### Requirement: spec module sub-command avoids collision with group command name

The system SHALL mount the `spec` module as the `api` sub-command within the `spec` category group to
avoid a name collision. The shipped migration window has ended; removed flat bundle shims SHALL NOT
be restored. This routing SHALL remain valid in either grouping mode, and project packages SHALL NOT
supply or replace the reserved `spec` root through category-less legacy registration.

#### Scenario: spec module mounts as `api` sub-command within spec group

- **GIVEN** the `specfact-spec` bundle is installed
- **WHEN** the user runs `specfact spec --help`
- **THEN** the spec module SHALL appear as `api` within the category group
- **AND** its sub-commands SHALL remain accessible through `specfact spec api <sub-command>`
- **AND** removed flat-shim delegation SHALL remain absent
