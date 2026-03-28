## MODIFIED Requirements

### Requirement: ToolCapabilities supports extension and preset metadata

The `ToolCapabilities` dataclass SHALL include optional fields for extensions, extension commands, presets, hook events, and version detection source.

#### Scenario: ToolCapabilities with extension metadata

- **GIVEN** a `ToolCapabilities` instance created for a spec-kit v0.4.x repository
- **WHEN** the instance is constructed with extension data
- **THEN** `extensions` is a `list[str]` of extension names (e.g., `["reconcile", "sync", "verify"]`)
- **AND** `extension_commands` is a `dict[str, list[str]]` mapping extension names to command lists
- **AND** `presets` is a `list[str]` of active preset names
- **AND** `hook_events` is a `list[str]` of detected hook event types
- **AND** `detected_version_source` is a `str` with value `"cli"` or `"heuristic"`

#### Scenario: ToolCapabilities backward compatibility

- **GIVEN** a `ToolCapabilities` instance created without the new optional fields
- **WHEN** the instance is constructed with only the existing fields (`tool`, `version`, `layout`, `specs_dir`, `has_external_config`, `has_custom_hooks`, `supported_sync_modes`)
- **THEN** `extensions` defaults to `None`
- **AND** `extension_commands` defaults to `None`
- **AND** `presets` defaults to `None`
- **AND** `hook_events` defaults to `None`
- **AND** `detected_version_source` defaults to `None`
- **AND** all existing adapter code continues to work without modification

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
