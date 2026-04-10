# bridge-registry Specification

## Purpose

TBD - created by archiving change arch-05-bridge-registry. Update Purpose after archive.

## Requirements

### Requirement: Bridge registry provides converter registration and lookup

The system SHALL provide a `BridgeRegistry` that supports module-driven registration and lookup of service schema converters.

#### Scenario: Register converter for service ID

- **WHEN** a module lifecycle registration step provides a valid bridge declaration
- **THEN** `BridgeRegistry` SHALL register the converter for the declared bridge ID
- **AND** the converter SHALL be retrievable by that same bridge ID.

#### Scenario: Lookup missing converter fails with explicit error

- **WHEN** code requests a converter for a bridge ID that is not registered
- **THEN** `BridgeRegistry` SHALL raise a clear lookup error
- **AND** the error SHALL include the missing bridge ID.

### Requirement: SchemaConverter protocol defines bidirectional conversion contract

The system SHALL provide a `SchemaConverter` protocol to standardize conversion between external service payloads and ProjectBundle-compatible data.

#### Scenario: Converter defines to_bundle contract

- **WHEN** a converter implements `SchemaConverter`
- **THEN** it SHALL implement `to_bundle(external_data: dict) -> dict`
- **AND** the returned payload SHALL be compatible with ProjectBundle construction.

#### Scenario: Converter defines from_bundle contract

- **WHEN** a converter implements `SchemaConverter`
- **THEN** it SHALL implement `from_bundle(bundle_data: dict) -> dict`
- **AND** the returned payload SHALL be service-specific output.

### Requirement: Bridge registry preserves core-module isolation

The system SHALL enforce bridge registration without introducing direct core imports from `specfact_cli.modules.*`.

#### Scenario: Core retrieves bridge via registry only

- **WHEN** core CLI workflows need a converter
- **THEN** they SHALL call `BridgeRegistry.get_converter()`
- **AND** SHALL NOT import converter implementations directly from module command packages.

#### Scenario: Invalid bridge declaration degrades gracefully

- **WHEN** module metadata declares an invalid converter class path
- **THEN** registration SHALL skip that bridge and log warning/debug context
- **AND** CLI startup SHALL continue for unaffected modules.

### Requirement: Bridge registration supports offline-first workflows

The system SHALL support bridge registration and local converter resolution without requiring network access.

#### Scenario: Offline startup with local manifests

- **WHEN** CLI starts in an offline environment
- **THEN** bridge registration SHALL complete using local module manifests and local Python imports
- **AND** SHALL NOT require external API or registry calls.

### Requirement: BridgeConfig spec-kit presets include all slash commands

The `BridgeConfig` spec-kit presets SHALL map all 7 core spec-kit slash commands.

#### Scenario: Classic preset includes full command set

- **GIVEN** `BridgeConfig.preset_speckit_classic()` is called
- **WHEN** the preset is constructed
- **THEN** `commands` dict contains entries for: `"specify"`, `"plan"`, `"tasks"`, `"implement"`, `"constitution"`, `"clarify"`, `"analyze"`
- **AND** each entry has a `trigger` matching the corresponding `/speckit.*` slash command
- **AND** each entry has appropriate `input_ref` and `output_ref` fields

#### Scenario: Specify preset includes full command set

- **GIVEN** `BridgeConfig.preset_speckit_specify()` is called
- **WHEN** the preset is constructed
- **THEN** `commands` dict contains the same 7 entries as the classic preset
- **AND** artifact path patterns use `.specify/specs/` prefix

#### Scenario: Modern preset includes full command set

- **GIVEN** `BridgeConfig.preset_speckit_modern()` is called
- **WHEN** the preset is constructed
- **THEN** `commands` dict contains the same 7 entries as the classic preset
- **AND** artifact path patterns use `docs/specs/` prefix
