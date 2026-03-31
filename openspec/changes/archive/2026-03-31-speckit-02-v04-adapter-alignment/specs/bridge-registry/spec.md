## ADDED Requirements

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
