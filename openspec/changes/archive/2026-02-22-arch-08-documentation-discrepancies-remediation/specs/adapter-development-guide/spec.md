# adapter-development-guide Specification

Adapter developers have a guide that describes the full BridgeAdapter interface, ToolCapabilities, and how to implement or extend adapters.

## ADDED Requirements

### Requirement: Full BridgeAdapter interface documented

The adapter development guide (or extended creating-custom-bridges) SHALL document the full BridgeAdapter interface: detect, import_artifact, export_artifact, load_change_tracking, save_change_tracking (or equivalent), with contracts and usage notes.

#### Scenario: Developer implements adapter

- **GIVEN** the adapter development guide (or extended creating-custom-bridges)
- **WHEN** a developer implements an adapter
- **THEN** the full BridgeAdapter interface is documented
- **AND** contracts and usage notes are provided

### Requirement: ToolCapabilities and adapter selection documented

The ToolCapabilities model and its role in adapter selection (e.g. sync modes) SHALL be documented, with reference to code (e.g. models/bridge.py) if needed.

#### Scenario: Developer declares or uses capabilities

- **GIVEN** the adapter documentation
- **WHEN** a developer needs to declare or use adapter capabilities
- **THEN** ToolCapabilities model is documented
- **AND** its role in adapter selection is explained

### Requirement: Examples or code references provided

The adapter guide SHALL provide at least one code reference or minimal example (e.g. base adapter, existing OpenSpec/SpecKit adapter) so that implementation is clear.

#### Scenario: Developer follows adapter guide

- **GIVEN** the adapter guide
- **WHEN** a developer follows the guide
- **THEN** at least one code reference or minimal example is provided
- **AND** implementation path is clear

### Requirement: Adapter guide discoverable

The adapter development content SHALL be reachable from the docs navigation and from bridge/architecture documentation.

#### Scenario: User looks for adapter development

- **GIVEN** the published docs
- **WHEN** a user looks for adapter or bridge development
- **THEN** the adapter development content is reachable from the docs navigation
- **AND** from bridge/architecture documentation
