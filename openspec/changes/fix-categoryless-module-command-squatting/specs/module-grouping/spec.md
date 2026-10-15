## MODIFIED Requirements

### Requirement: Registry groups modules by category when loading

The registry SHALL read category metadata and group categorized modules. Missing-category project packages SHALL be
skipped in default grouped mode; other discovery sources and explicit legacy mode retain flat registration, except
permanent core commands reserved by the runtime-validation contract.

#### Scenario: Registry collects category groups from installed modules

- **GIVEN** `category_grouping_enabled` is `true` (default)
- **WHEN** the registry initialises and scans installed modules
- **THEN** it SHALL produce a `dict[str, list[ModulePackage]]` mapping each `bundle_group_command` to its member
modules
- **AND** SHALL treat `core` category modules as ungrouped top-level commands

#### Scenario: Registry falls back to flat mounting when grouping disabled

- **GIVEN** `category_grouping_enabled` is explicitly `false`
- **AND** a project module omits category and declares an unreserved root command
- **WHEN** commands are registered
- **THEN** the declared command SHALL retain flat registration
- **AND** categorized modules SHALL retain their current category registration

#### Scenario: Module with missing category fields is handled gracefully

- **GIVEN** a manifest omits category without an inferable legacy group
- **WHEN** the registry reads the manifest
- **THEN** it SHALL retain missing category without granting core authority
- **AND** SHALL warn without preventing startup
- **AND** command registration SHALL apply the discovery-source and grouping policy

#### Scenario: Category-less workspace module cannot claim a root command

- **GIVEN** default grouped mode and a discovered project module with no category
- **WHEN** package commands are registered
- **THEN** no declared root command SHALL be registered
- **AND** its loader SHALL NOT execute through those commands

#### Scenario: Non-workspace legacy module remains supported

- **GIVEN** a user, marketplace or custom package omits category and declares an unreserved command
- **WHEN** grouped-mode commands are registered
- **THEN** legacy flat registration SHALL remain available for that source

#### Scenario: Rejected workspace package has no registration side effects

- **GIVEN** a project package rejected by the root-command policy
- **WHEN** another eligible package lazily imports a Python dependency
- **THEN** the rejected package SHALL NOT enter active import roots or shadow that dependency
- **AND** SHALL NOT register schema extensions, service bridges or category mounts
