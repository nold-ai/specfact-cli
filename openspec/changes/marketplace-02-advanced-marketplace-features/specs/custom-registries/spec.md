# custom-registries Specification

## Purpose

Defines support for multiple registry sources with trust levels and priority ordering.

## ADDED Requirements

### Requirement: Support multiple registries with priority ordering

The system SHALL manage multiple registries with configurable priority and trust levels.

#### Scenario: Add custom registry
- **WHEN** user runs `specfact module add-registry https://registry.company.com/index.json --id enterprise`
- **THEN** system SHALL add registry to ~/.specfact/config/registries.yaml
- **AND** SHALL assign next priority number
- **AND** SHALL set trust level to "prompt" by default

#### Scenario: List registries
- **WHEN** user runs `specfact module list-registries`
- **THEN** system SHALL display all configured registries
- **AND** SHALL show: id, url, priority, trust level

#### Scenario: Remove registry
- **WHEN** user runs `specfact module remove-registry enterprise`
- **THEN** system SHALL remove registry from config
- **AND** SHALL NOT affect modules already installed from that registry

### Requirement: Module search queries all registries

The system SHALL search across all configured registries in priority order.

#### Scenario: Search returns results from multiple registries
- **WHEN** user runs `specfact module search backlog`
- **THEN** system SHALL fetch indexes from all registries
- **AND** SHALL aggregate results
- **AND** SHALL indicate source registry for each result

### Requirement: Trust levels control module installation

The system SHALL enforce trust levels during module installation.

#### Scenario: Install from trusted registry (always)
- **WHEN** installing module from trust=always registry
- **THEN** system SHALL proceed without prompt

#### Scenario: Install from untrusted registry (prompt)
- **WHEN** installing module from trust=prompt registry
- **THEN** system SHALL display warning and registry info
- **AND** SHALL prompt user for confirmation
