## MODIFIED Requirements

### Requirement: Spec-Kit Adapter Implementation

The system SHALL provide a `SpecKitAdapter` class that encapsulates all Spec-Kit-specific logic, including comprehensive tool capabilities detection for v0.4.x features. The `ToolCapabilities` dataclass SHALL include optional fields for extensions, extension commands, presets, hook events, and version detection source.

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

#### Scenario: Get capabilities for spec-kit v0.4.x repository

- **GIVEN** a repository with `.specify/` directory, `extensions/catalog.community.json`, and `presets/` directory
- **WHEN** `SpecKitAdapter.get_capabilities(repo_path)` is called
- **THEN** returns `ToolCapabilities` with:
  - `tool` equals `"speckit"`
  - `version` populated from CLI or heuristic detection
  - `layout` equals `"modern"`
  - `extensions` contains list of detected extension names
  - `extension_commands` contains dict mapping extension names to their commands
  - `presets` contains list of detected preset names
  - `hook_events` contains list of detected hook event types (e.g., `["before_task", "after_task"]`)
  - `detected_version_source` equals `"cli"` or `"heuristic"`
  - `supported_sync_modes` includes `"bidirectional"` and `"unidirectional"`

#### Scenario: Get capabilities for legacy spec-kit repository

- **GIVEN** a repository with only `specs/` directory at root (no `.specify/`, no `extensions/`, no `presets/`)
- **WHEN** `SpecKitAdapter.get_capabilities(repo_path)` is called
- **THEN** returns `ToolCapabilities` with:
  - `tool` equals `"speckit"`
  - `version` equals `None`
  - `layout` equals `"classic"`
  - `extensions` equals `None`
  - `extension_commands` equals `None`
  - `presets` equals `None`
  - `hook_events` equals `None`
  - `detected_version_source` equals `None`
- **AND** behavior is identical to the pre-change adapter

#### Scenario: Get capabilities with cross-repo bridge config

- **GIVEN** a bridge config with `external_base_path` pointing to a spec-kit repository
- **WHEN** `SpecKitAdapter.get_capabilities(repo_path, bridge_config)` is called
- **THEN** extension and preset detection uses the `external_base_path` as base
- **AND** CLI version detection is skipped for cross-repo scenarios (filesystem-only)

## MODIFIED Requirements: Repository Detection

### Requirement: SpecKitAdapter detect identifies spec-kit repositories

The system SHALL detect spec-kit repositories including those with the new extension and preset directories.

#### Scenario: Detect spec-kit repository with extensions directory

- **GIVEN** a repository with `.specify/specs/` and `extensions/` directories
- **WHEN** `SpecKitAdapter.detect(repo_path)` is called
- **THEN** returns `True`

#### Scenario: Detect spec-kit repository with presets directory

- **GIVEN** a repository with `.specify/specs/` and `presets/` directories
- **WHEN** `SpecKitAdapter.detect(repo_path)` is called
- **THEN** returns `True`
