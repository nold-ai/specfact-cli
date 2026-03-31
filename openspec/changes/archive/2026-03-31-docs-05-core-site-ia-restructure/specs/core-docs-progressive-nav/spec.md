# Capability: core-docs-progressive-nav

Core docs site sidebar provides a 6-section progressive navigation structure.

## ADDED Requirements

### Requirement: Sidebar provides 6-section progressive navigation

The system SHALL provide a sidebar with 6 sections in a specific order.

#### Scenario: Sidebar renders 6 sections in correct order

- **GIVEN** the core docs site is built with Jekyll
- **WHEN** a user visits any page on docs.specfact.io
- **THEN** the sidebar displays sections in order: Getting Started, Core CLI, Module System, Architecture, Reference, Migration

#### Scenario: Getting Started section contains beginner-friendly entries

- **GIVEN** the sidebar Getting Started section
- **WHEN** a user expands the section
- **THEN** it contains: Installation, 5-Minute Quickstart, Profiles & IDE Setup
- **AND** does NOT contain module-specific tutorials (backlog quickstart, standup, refine)

#### Scenario: Core CLI section links to command reference pages

- **GIVEN** the sidebar Core CLI section
- **WHEN** a user expands the section
- **THEN** it contains links to: specfact init, specfact module, specfact upgrade, Operational Modes, Debug Logging

#### Scenario: Moved files redirect to new locations

- **GIVEN** a file was moved from its old location
- **WHEN** a user visits the old URL
- **THEN** they are redirected to the new URL via jekyll-redirect-from
