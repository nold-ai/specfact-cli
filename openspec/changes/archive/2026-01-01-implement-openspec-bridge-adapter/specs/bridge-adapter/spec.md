# Bridge Adapter Capability

## ADDED Requirements

### Requirement: OpenSpec Adapter Type

The system SHALL support OpenSpec as a bridge adapter type.

#### Scenario: Add OpenSpec to AdapterType Enum

- **GIVEN** the bridge adapter architecture
- **WHEN** OpenSpec adapter type is added
- **THEN** `AdapterType.OPENSPEC` enum value exists
- **AND** enum value equals "openspec"
- **AND** OpenSpec is included in supported adapters list

#### Scenario: OpenSpec Preset Configuration

- **GIVEN** a bridge configuration needs OpenSpec preset
- **WHEN** `BridgeConfig.preset_openspec()` is called
- **THEN** returns `BridgeConfig` with:
  - `adapter = AdapterType.OPENSPEC`
  - Artifact mappings for:
    - `specification`: `openspec/specs/{feature_id}/spec.md`
    - `project_context`: `openspec/project.md`
    - `change_proposal`: `openspec/changes/{change_name}/proposal.md`
    - `change_tasks`: `openspec/changes/{change_name}/tasks.md`
    - `change_spec_delta`: `openspec/changes/{change_name}/specs/{feature_id}/spec.md`

### Requirement: Cross-Repository Support

The system SHALL support OpenSpec in different repositories via `external_base_path` configuration.

#### Scenario: Configure Cross-Repository OpenSpec

- **GIVEN** OpenSpec is in a different repository than code being analyzed
- **WHEN** bridge config includes `external_base_path`
- **THEN** all OpenSpec paths resolve relative to external base path
- **AND** detection checks external path first
- **AND** parsing uses external path for all artifacts

#### Scenario: Same-Repository OpenSpec (Default)

- **GIVEN** OpenSpec is in same repository as code
- **WHEN** bridge config has no `external_base_path`
- **THEN** all OpenSpec paths resolve relative to repository root
- **AND** detection checks same-repo location

### Requirement: OpenSpec Detection

The system SHALL detect OpenSpec installations (same-repo and cross-repo).

#### Scenario: Detect Same-Repository OpenSpec

- **GIVEN** a repository with `openspec/` directory
- **WHEN** `BridgeProbe.detect()` is called
- **THEN** detects OpenSpec if:
  - `openspec/project.md` exists
  - `openspec/specs/` directory exists
- **AND** returns `ToolCapabilities` with `tool="openspec"`

#### Scenario: Detect Cross-Repository OpenSpec

- **GIVEN** bridge config with `external_base_path` pointing to OpenSpec repo
- **WHEN** `BridgeProbe.detect()` is called
- **THEN** checks external path for OpenSpec structure
- **AND** detects OpenSpec if external path has `openspec/project.md` and `openspec/specs/`
- **AND** returns `ToolCapabilities` with `tool="openspec"`

#### Scenario: Auto-Generate Bridge Config for OpenSpec

- **GIVEN** OpenSpec is detected
- **WHEN** `BridgeProbe.auto_generate_bridge()` is called
- **THEN** returns `BridgeConfig.preset_openspec()`
- **AND** includes `external_base_path` if cross-repo detected

### Requirement: OpenSpec Parser

The system SHALL parse OpenSpec format files (project.md, specs/, changes/).

#### Scenario: Parse Project Context

- **GIVEN** an OpenSpec `project.md` file
- **WHEN** `OpenSpecParser.parse_project_md(path)` is called
- **THEN** parses markdown sections:
  - Purpose
  - Tech Stack
  - Project Conventions
  - Domain Context
  - Constraints
  - External Dependencies
- **AND** returns structured dict with parsed content
- **AND** handles missing file gracefully (returns None or empty dict)

#### Scenario: Parse Feature Specification

- **GIVEN** an OpenSpec spec file `openspec/specs/{feature}/spec.md`
- **WHEN** `OpenSpecParser.parse_spec_md(path)` is called
- **THEN** parses feature specification markdown
- **AND** extracts requirements and scenarios
- **AND** returns structured dict with feature data

#### Scenario: Parse Change Proposal

- **GIVEN** an OpenSpec change proposal `openspec/changes/{change}/proposal.md`
- **WHEN** `OpenSpecParser.parse_change_proposal(path)` is called
- **THEN** parses proposal sections:
  - Why (rationale)
  - What Changes (description)
  - Impact (affected code/specs)
- **AND** returns structured dict with proposal data

#### Scenario: Parse Delta Spec

- **GIVEN** an OpenSpec delta spec `openspec/changes/{change}/specs/{feature}/spec.md`
- **WHEN** `OpenSpecParser.parse_change_spec_delta(path)` is called
- **THEN** parses ADDED/MODIFIED/REMOVED markers
- **AND** extracts change type (ADDED, MODIFIED, REMOVED)
- **AND** extracts changed content
- **AND** returns structured dict with delta metadata

#### Scenario: List Active Changes

- **GIVEN** an OpenSpec changes directory
- **WHEN** `OpenSpecParser.list_active_changes(repo_path)` is called
- **THEN** lists all change directories in `openspec/changes/`
- **AND** excludes archive directory
- **AND** supports cross-repo paths via bridge config

### Requirement: Read-Only Sync

The system SHALL import OpenSpec artifacts into SpecFact (read-only, no writes to OpenSpec).

#### Scenario: Import OpenSpec Specification

- **GIVEN** an OpenSpec spec file
- **WHEN** `BridgeSync._import_openspec_artifact("specification", path, bundle)` is called
- **THEN** parses spec using `OpenSpecParser.parse_spec_md()`
- **AND** maps to SpecFact `Feature` model
- **AND** stores OpenSpec path in `source_tracking.source_metadata`
- **AND** adds feature to bundle

#### Scenario: Import OpenSpec Project Context

- **GIVEN** an OpenSpec `project.md` file
- **WHEN** `BridgeSync._import_openspec_artifact("project_context", path, bundle)` is called
- **THEN** parses project context using `OpenSpecParser.parse_project_md()`
- **AND** maps to SpecFact aspects (Idea, Business, Product)
- **AND** stores conventions in `BundleManifest.bundle.metadata`
- **AND** stores OpenSpec path in `source_tracking`

#### Scenario: Import OpenSpec Change Proposal

- **GIVEN** an OpenSpec change proposal
- **WHEN** `BridgeSync._import_openspec_artifact("change_proposal", path, bundle)` is called
- **THEN** parses proposal using `OpenSpecParser.parse_change_proposal()`
- **AND** maps to `ChangeProposal` model (from change tracking data model)
- **AND** stores OpenSpec path in `source_tracking`
- **AND** adds to bundle's change tracking

#### Scenario: Import OpenSpec Delta Spec

- **GIVEN** an OpenSpec delta spec
- **WHEN** `BridgeSync._import_openspec_artifact("change_spec_delta", path, bundle)` is called
- **THEN** parses delta using `OpenSpecParser.parse_change_spec_delta()`
- **AND** maps to `FeatureDelta` model (from change tracking data model)
- **AND** stores OpenSpec path in `source_tracking`
- **AND** adds to bundle's change tracking

### Requirement: Alignment Report Generation

The system SHALL generate alignment reports comparing SpecFact features vs OpenSpec specs.

#### Scenario: Generate Alignment Report

- **GIVEN** SpecFact bundle and OpenSpec specs have been imported
- **WHEN** `BridgeSync.generate_alignment_report()` is called
- **THEN** compares SpecFact features vs OpenSpec specs
- **AND** identifies gaps (OpenSpec specs not in SpecFact)
- **AND** calculates coverage percentage (SpecFact features / OpenSpec specs)
- **AND** generates markdown report with:
  - Feature comparison table
  - Gap list (OpenSpec specs not extracted)
  - Coverage percentage
  - Recommendations

#### Scenario: Report Coverage Calculation

- **GIVEN** SpecFact has 8 features and OpenSpec has 10 specs
- **WHEN** alignment report is generated
- **THEN** coverage is calculated as 8/10 = 80%
- **AND** report lists 2 missing features from OpenSpec

### Requirement: CLI Command Support

The system SHALL support OpenSpec adapter in sync bridge CLI command.

#### Scenario: Sync Bridge with OpenSpec Adapter

- **GIVEN** OpenSpec is detected in repository
- **WHEN** user runs `specfact sync bridge --adapter openspec --mode read-only --bundle BUNDLE`
- **THEN** command accepts "openspec" as adapter type
- **AND** performs read-only sync (imports OpenSpec artifacts)
- **AND** generates alignment report
- **AND** outputs report to console and/or file

#### Scenario: Auto-Detect OpenSpec Adapter

- **GIVEN** OpenSpec is detected in repository
- **WHEN** user runs `specfact sync bridge --bundle BUNDLE` (no adapter specified)
- **THEN** auto-detects OpenSpec adapter
- **AND** uses OpenSpec for sync
- **AND** informs user of detected adapter
