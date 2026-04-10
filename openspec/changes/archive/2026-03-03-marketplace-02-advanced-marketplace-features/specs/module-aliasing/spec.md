# module-aliasing Specification

## Purpose

Defines user-configurable aliases mapping command names to namespaced module IDs for convenience.

## ADDED Requirements

### Requirement: Alias system maps commands to namespaced modules

The system SHALL provide alias commands to create, list, and remove command-to-module mappings.

#### Scenario: Create alias

- **WHEN** user runs `specfact module alias backlog acme-corp/backlog-pro`
- **THEN** system SHALL store mapping in ~/.specfact/registry/aliases.json
- **AND** SHALL display success message
- **AND** SHALL resolve "backlog" command to "acme-corp/backlog-pro" module

#### Scenario: List aliases

- **WHEN** user runs `specfact module alias list`
- **THEN** system SHALL display all configured aliases
- **AND** SHALL show format: "alias -> namespaced-id"

#### Scenario: Remove alias

- **WHEN** user runs `specfact module alias remove backlog`
- **THEN** system SHALL delete alias from aliases.json
- **AND** SHALL revert to default resolution (specfact/backlog)

### Requirement: Command resolution checks aliases before defaults

The system SHALL resolve command names through alias system before falling back to defaults.

#### Scenario: Aliased command resolved

- **WHEN** alias "backlog" maps to "acme-corp/backlog-pro"
- **AND** user runs backlog command
- **THEN** system SHALL load acme-corp/backlog-pro module

#### Scenario: Alias warns when shadowing built-in

- **WHEN** user creates alias for built-in module name
- **THEN** system SHALL warn "Alias will shadow built-in module"
- **AND** SHALL require --force flag to proceed
