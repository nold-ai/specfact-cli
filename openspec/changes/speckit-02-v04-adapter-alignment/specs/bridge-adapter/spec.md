## MODIFIED Requirements

### Requirement: SpecKitAdapter get_capabilities returns tool metadata

The system SHALL return comprehensive tool capabilities including extension metadata, preset information, and hook events when detecting a spec-kit installation.

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

## MODIFIED Requirements

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
