# bridge-adapter Specification

## Purpose

The bridge adapter architecture provides a universal abstraction layer for integrating SpecFact with external tools and formats, including specification tools (Spec-Kit, OpenSpec), backlog management tools (GitHub Issues, Azure DevOps, Jira, Linear), and validation systems. The architecture uses a plugin-based adapter registry pattern that enables extensibility for future tool integrations while maintaining clean separation of concerns.
## Requirements
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
    - `project_context`: `openspec/config.yaml` (OPSX) if present, else `openspec/project.md` (legacy)
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
  - `openspec/config.yaml` exists (OPSX), or
  - `openspec/project.md` exists (legacy), or
  - `openspec/specs/` directory exists
- **AND** returns `ToolCapabilities` with `tool="openspec"`

#### Scenario: Detect Cross-Repository OpenSpec

- **GIVEN** bridge config with `external_base_path` pointing to OpenSpec repo
- **WHEN** `BridgeProbe.detect()` is called
- **THEN** checks external path for OpenSpec structure
- **AND** detects OpenSpec if external path has `openspec/config.yaml` (OPSX) or `openspec/project.md` (legacy), and `openspec/specs/`
- **AND** returns `ToolCapabilities` with `tool="openspec"`

#### Scenario: Auto-Generate Bridge Config for OpenSpec

- **GIVEN** OpenSpec is detected
- **WHEN** `BridgeProbe.auto_generate_bridge()` is called
- **THEN** returns `BridgeConfig.preset_openspec()`
- **AND** includes `external_base_path` if cross-repo detected

### Requirement: OpenSpec Parser

The system SHALL parse OpenSpec format files (config.yaml or project.md for project context, specs/, changes/).

#### Scenario: Parse Project Context (OPSX or Legacy)

- **GIVEN** an OpenSpec project context file: `openspec/config.yaml` (OPSX) or `openspec/project.md` (legacy)
- **WHEN** project context is imported (adapter resolves to config.yaml if present, else project.md)
- **THEN** for config.yaml: `OpenSpecParser.parse_config_yaml(path)` parses `context:` (and optional `rules:`)
- **AND** for project.md: `OpenSpecParser.parse_project_md(path)` parses markdown sections (Purpose, Tech Stack, Conventions, Context, Constraints, Dependencies)
- **AND** returns structured dict compatible with Idea/narrative update
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

- **GIVEN** an OpenSpec project context file (path resolved to `openspec/config.yaml` if present, else `openspec/project.md`)
- **WHEN** `BridgeSync` imports `project_context` (adapter receives resolved path)
- **THEN** parses using `OpenSpecParser.parse_config_yaml(path)` for config.yaml or `OpenSpecParser.parse_project_md(path)` for project.md
- **AND** maps to SpecFact aspects (Idea narrative, etc.)
- **AND** stores conventions in bundle metadata
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

### Requirement: Universal Abstraction Layer for Bridge Adapters

The system SHALL use a plugin-based adapter registry pattern for all tool integrations, with no hard-coded adapter checks in core sync/probe logic.

#### Scenario: Spec-Kit Adapter Registration

- **GIVEN** the bridge adapter architecture
- **WHEN** Spec-Kit adapter is implemented
- **THEN** `SpecKitAdapter` class implements `BridgeAdapter` interface
- **AND** adapter is registered via `AdapterRegistry.register("speckit", SpecKitAdapter)`
- **AND** adapter is accessible via `AdapterRegistry.get_adapter("speckit")`
- **AND** all Spec-Kit logic is encapsulated in `SpecKitAdapter` class

#### Scenario: Adapter-Agnostic Sync Command

- **GIVEN** the `specfact sync bridge` command
- **WHEN** sync command executes for any adapter
- **THEN** uses `AdapterRegistry.get_adapter()` to retrieve adapter
- **AND** uses `BridgeSync` class for sync operations
- **AND** contains no hard-coded `if adapter_type == AdapterType.SPECKIT:` checks
- **AND** contains no direct instantiation of adapter-specific classes (SpecKitSync, SpecKitConverter, SpecKitScanner)

#### Scenario: Adapter-Agnostic Bridge Probe

- **GIVEN** the `BridgeProbe` class
- **WHEN** bridge validation is performed
- **THEN** `validate_bridge()` method contains no hard-coded adapter checks
- **AND** adapter-specific validation suggestions are provided by adapters themselves
- **AND** probe uses adapter registry for all adapter operations

#### Scenario: Adapter-Agnostic Bridge Sync

- **GIVEN** the `BridgeSync` class
- **WHEN** alignment report or other adapter-specific operations are performed
- **THEN** contains no hard-coded adapter value checks (e.g., `adapter.value != "openspec"`)
- **AND** adapter-specific operations are handled via adapter interface methods
- **AND** sync uses adapter registry for all adapter operations
- **AND** adapter-specific kwargs are determined via adapter capabilities, not hard-coded checks

#### Scenario: Adapter-Agnostic Import Command

- **GIVEN** the `specfact import from-bridge` command
- **WHEN** import command executes for any adapter
- **THEN** uses `AdapterRegistry.get_adapter()` to retrieve adapter
- **AND** uses `BridgeSync` class for import operations
- **AND** contains no hard-coded `if adapter_type == AdapterType.SPECKIT:` checks
- **AND** contains no direct instantiation of adapter-specific classes (SpecKitScanner, SpecKitConverter)
- **AND** uses adapter's `detect()` method instead of tool-specific detection methods

#### Scenario: Adapter-Agnostic Sync Mode Detection

- **GIVEN** the `specfact sync bridge` command
- **WHEN** sync mode is auto-detected
- **THEN** uses adapter's `get_capabilities()` to determine supported sync modes
- **AND** contains no hard-coded adapter type lists (e.g., `devops_adapters = ("github", "ado", "linear", "jira")`)
- **AND** contains no hard-coded mode assignments (e.g., `elif adapter_value == "openspec": sync_mode = "read-only"`)
- **AND** sync mode is determined by adapter capabilities, not hard-coded checks

### Requirement: Spec-Kit Adapter Implementation

The system SHALL provide a `SpecKitAdapter` class that encapsulates all Spec-Kit-specific logic.

#### Scenario: Spec-Kit Detection

- **GIVEN** a repository with Spec-Kit structure
- **WHEN** `SpecKitAdapter.detect()` is called
- **THEN** checks for `.specify/` directory (indicates Spec-Kit project)
- **AND** checks for `specs/` directory (classic format) or `docs/specs/` directory (modern format)
- **AND** checks for `.specify/memory/constitution.md` file
- **AND** returns True if Spec-Kit structure is detected (`.specify/` directory exists)
- **AND** supports cross-repo detection via `bridge_config.external_base_path`

#### Scenario: Spec-Kit Capabilities

- **GIVEN** Spec-Kit is detected
- **WHEN** `SpecKitAdapter.get_capabilities()` is called
- **THEN** returns `ToolCapabilities` with:
  - `tool="speckit"`
  - `specs_dir` set to detected format (`specs/` for classic, `docs/specs/` for modern)
  - `has_custom_hooks` flag based on constitution presence and validation (non-minimal constitution)
  - `layout` set to "standard" (Spec-Kit uses standard layout)
- **AND** validates constitution exists and is not minimal (empty or template-only)
- **AND** supports cross-repo paths via bridge_config

#### Scenario: Spec-Kit Artifact Import

- **GIVEN** Spec-Kit artifacts exist in repository
- **WHEN** `SpecKitAdapter.import_artifact()` is called
- **THEN** uses `SpecKitScanner` and `SpecKitConverter` internally
- **AND** maps Spec-Kit artifacts (spec.md, plan.md, tasks.md) to SpecFact models
- **AND** stores Spec-Kit paths in `source_tracking.source_metadata`
- **AND** supports both modern (`.specify/`) and classic (`specs/`) formats

#### Scenario: Spec-Kit Artifact Export

- **GIVEN** SpecFact project bundle with features
- **WHEN** `SpecKitAdapter.export_artifact()` is called
- **THEN** uses `SpecKitConverter.convert_to_speckit()` internally
- **AND** exports SpecFact features to Spec-Kit format (spec.md, plan.md, tasks.md)
- **AND** supports overwrite mode and conflict resolution
- **AND** writes to correct format based on detected Spec-Kit structure

#### Scenario: Spec-Kit Bridge Config Generation

- **GIVEN** Spec-Kit is detected
- **WHEN** `SpecKitAdapter.generate_bridge_config()` is called
- **THEN** returns `BridgeConfig` using existing preset methods:
  - `BridgeConfig.preset_speckit_classic()` if classic format detected (`specs/` directory at root)
  - `BridgeConfig.preset_speckit_modern()` if modern format detected (`docs/specs/` directory)
  - Artifact mappings include: `specification`, `plan`, `tasks`, `contracts`
  - Constitution path: `.specify/memory/constitution.md` (checked for both formats)
- **AND** includes `external_base_path` if cross-repo detected
- **AND** auto-detects format based on directory structure (classic: `specs/` at root, modern: `docs/specs/`)

#### Scenario: Spec-Kit Bidirectional Sync

- **GIVEN** Spec-Kit adapter is used for bidirectional sync
- **WHEN** `BridgeSync.sync_bidirectional()` is called with Spec-Kit adapter
- **THEN** adapter's `import_artifact()` and `export_artifact()` methods handle change detection internally
- **AND** adapter detects changes in Spec-Kit artifacts (via internal `_detect_speckit_changes()` helper)
- **AND** adapter detects changes in SpecFact artifacts (via internal `_detect_specfact_changes()` helper)
- **AND** adapter merges changes and detects conflicts (via internal `_merge_changes()` and `_detect_conflicts()` helpers)
- **AND** conflicts are resolved using priority rules (SpecFact > Spec-Kit for artifacts)

#### Scenario: Spec-Kit Constitution Validation

- **GIVEN** Spec-Kit adapter is used
- **WHEN** `SpecKitAdapter.get_capabilities()` is called
- **THEN** checks for constitution file (`.specify/memory/constitution.md` or classic format)
- **AND** sets `has_custom_hooks` flag based on constitution presence
- **AND** validates constitution is not minimal (if present)
- **AND** returns `ToolCapabilities` with constitution validation status

#### Scenario: Constitution Command Location

- **GIVEN** Spec-Kit constitution management commands exist
- **WHEN** user wants to manage constitution
- **THEN** commands are available via `specfact sdd constitution` (not `specfact bridge constitution`)
- **AND** `specfact bridge` command does not exist (bridge adapters are internal connectors, no user-facing commands)
- **AND** constitution commands (bootstrap, enrich, validate) are under SDD command group (Spec-Kit is an SDD tool)

### Requirement: Backlog Adapter Extensibility Pattern

The bridge adapter architecture SHALL provide reusable patterns and abstractions that enable easy implementation of future backlog adapters (Azure DevOps/ADO, Jira, Linear, etc.) following the same patterns as the GitHub adapter implementation.

#### Scenario: Future backlog adapters follow established patterns

- **WHEN** a new backlog adapter is implemented (ADO, Jira, Linear, etc.)
- **THEN** it follows the same import/export patterns as GitHub adapter
- **AND** it uses the same tool-agnostic status mapping interface
- **AND** it uses the same tool-agnostic metadata extraction interface
- **AND** it stores tool-specific metadata in `source_tracking` only
- **AND** it respects `bridge_config.external_base_path` for cross-repo support

### Requirement: Backlog Adapter Import Capability

The bridge adapter architecture SHALL support importing backlog items (issues, work items, tickets) from backlog management tools as OpenSpec change proposals. GitHub is the first implementation; the pattern must be extensible for future backlog adapters (Azure DevOps/ADO, Jira, Linear, etc.).

#### Scenario: Import backlog item as change proposal (GitHub first)

- **WHEN** a backlog item is imported via `import_artifact("github_issue", issue_data, project_bundle, bridge_config)` (GitHub)
- **OR** via `import_artifact("ado_work_item", ...)` (future: Azure DevOps)
- **OR** via `import_artifact("jira_issue", ...)` (future: Jira)
- **OR** via `import_artifact("linear_issue", ...)` (future: Linear)
- **THEN** the backlog item body is parsed to extract change proposal data (title, description, rationale)
- **AND** backlog item status/labels are mapped to OpenSpec change status (tool-agnostic mapping)
- **AND** backlog item metadata (ID, URL, status, assignees) is stored in `source_tracking` (tool-agnostic pattern)

#### Scenario: Handle missing or malformed backlog item data

- **WHEN** backlog item data is missing required fields or malformed (any backlog adapter)
- **THEN** the import method raises `ValueError` with descriptive error message
- **AND** no change proposal is created

#### Scenario: Map backlog status to OpenSpec status (tool-agnostic pattern)

- **WHEN** backlog item has status "enhancement" or "new" or "todo" (GitHub label, ADO state, Jira status, Linear state)
- **THEN** OpenSpec change status is set to "proposed"
- **WHEN** backlog item has status "in-progress" or "active" or "in development"
- **THEN** OpenSpec change status is set to "in-progress"
- **WHEN** backlog item has status "done" or "closed" or "completed"
- **THEN** OpenSpec change status is set to "applied"
- **NOTE**: Status mapping must be tool-agnostic and configurable for future backlog adapters

### Requirement: Bidirectional Status Synchronization

Backlog adapters SHALL support bidirectional synchronization of change status between OpenSpec and backlog management tools. GitHub is the first implementation; the pattern must be extensible for future backlog adapters (ADO, Jira, Linear, etc.).

#### Scenario: Sync OpenSpec status to backlog status (tool-agnostic)

- **WHEN** OpenSpec change proposal status changes to "in-progress"
- **THEN** corresponding backlog item status is updated (GitHub labels, ADO state, Jira status, Linear state)
- **AND** previous status is removed/updated
- **NOTE**: Status sync pattern must be tool-agnostic and reusable for future backlog adapters

#### Scenario: Sync backlog status to OpenSpec status (tool-agnostic)

- **WHEN** backlog item status changes (e.g., GitHub "enhancement" → "in-progress", ADO "New" → "Active", Jira "To Do" → "In Progress", Linear "Backlog" → "In Progress")
- **THEN** corresponding OpenSpec change proposal status is updated
- **AND** change tracking is saved back to OpenSpec

#### Scenario: Handle status conflicts (tool-agnostic)

- **WHEN** OpenSpec status and backlog item status differ (any backlog adapter)
- **THEN** conflict resolution strategy is applied (prefer OpenSpec status or user-defined strategy)
- **AND** both systems are synchronized

### Requirement: Backlog Adapter Export and Import Capability

Backlog adapters SHALL support exporting OpenSpec change proposals to backlog management tools, **AND** importing backlog items as OpenSpec change proposals. GitHub is the first implementation; the pattern must be extensible for future backlog adapters (ADO, Jira, Linear, etc.).

#### Scenario: Export change proposal to backlog (tool-agnostic)

- **WHEN** a change proposal is exported via `export_artifact("change_proposal", proposal, bridge_config)`
- **THEN** a backlog item is created (GitHub issue, ADO work item, Jira issue, Linear issue)
- **AND** backlog item title and description are set from proposal
- **AND** backlog item status is set based on OpenSpec change status (tool-agnostic mapping)
- **AND** backlog item metadata is stored in `source_tracking` (tool-agnostic pattern)

#### Scenario: Export and import maintain bidirectional sync

- **WHEN** a change proposal is exported to GitHub and then imported back
- **THEN** the imported proposal matches the original proposal
- **AND** bidirectional sync is maintained

### Requirement: Validation Integration with Change Proposals

The SpecFact validation command SHALL integrate with OpenSpec change proposals to validate against proposed specifications.

#### Scenario: Load active change proposals during validation

- **WHEN** `specfact validate` command is executed in a repository with OpenSpec
- **THEN** active change proposals (status: "proposed" or "in-progress") are loaded
- **AND** associated spec deltas are extracted from change proposals

#### Scenario: Merge specs for validation

- **WHEN** active change proposals contain spec deltas
- **THEN** current Spec-Kit specs are merged with proposed OpenSpec changes
- **AND** ADDED requirements are included in validation set
- **AND** MODIFIED requirements replace existing requirements
- **AND** REMOVED requirements are excluded from validation set

#### Scenario: Update validation status in change proposals

- **WHEN** validation completes for a change proposal
- **THEN** `validation_status` in `FeatureDelta` is updated ("passed" or "failed")
- **AND** `validation_results` are stored with detailed validation output
- **AND** updated change tracking is saved back to OpenSpec

#### Scenario: Report validation results to backlog (tool-agnostic)

- **WHEN** validation completes and a backlog adapter is configured (GitHub, future: ADO, Jira, Linear)
- **THEN** validation results are reported to corresponding backlog item
- **AND** backlog item comments/notes are updated with validation status
- **AND** backlog item status/labels are updated based on validation status
- **NOTE**: Reporting pattern must be tool-agnostic and reusable for future backlog adapters

### Requirement: Azure DevOps Backlog Adapter

The Azure DevOps adapter SHALL use centralized authentication helper methods and SHALL support automatic token refresh. All ADO API requests SHALL use `_auth_headers()` helper method for consistent authentication. The ADO adapter SHALL attempt automatic token refresh when OAuth tokens expire. The ADO adapter SHALL support both PAT (Basic auth) and OAuth (Bearer auth) tokens. Error messages SHALL provide helpful guidance for authentication issues.

The ADO adapter SHALL ensure organization is always included before project in API URL paths for project-based permissions. URL construction SHALL always include `{org}/{project}` in path before `_apis/` endpoint. This ensures project-based permissions work correctly in larger organizations. This requirement SHALL apply to both cloud (Azure DevOps Services) and on-premise (Azure DevOps Server) configurations.

#### Scenario: Consistent Authentication Headers

**Given** an ADO adapter instance with a valid API token  
**When** the adapter makes any API request (WIQL query, work items batch GET, work item PATCH)  
**Then** the Authorization header must be constructed using `_auth_headers()` helper method  
**And** PAT tokens must be base64-encoded for Basic authentication  
**And** OAuth tokens must use Bearer authentication

#### Scenario: Automatic Token Refresh

**Given** an ADO adapter with an expired OAuth token stored  
**When** the adapter attempts to use the expired token  
**Then** the adapter must attempt to refresh the token using persistent token cache  
**And** if refresh succeeds, the adapter must update the stored token  
**And** if refresh fails, the adapter must provide helpful error messages with guidance

#### Scenario: PAT Token Support

**Given** an ADO adapter initialized with a PAT token (via `--pat` option or environment variable)  
**When** the adapter makes API requests  
**Then** the adapter must use Basic authentication with base64-encoded PAT  
**And** the adapter must not track PAT expiration (expiration managed by Azure DevOps)

#### Scenario: Project-Based Permissions URL Format

**Given** an ADO adapter configured with org and project  
**When** the adapter constructs API URLs  
**Then** the URL must follow format: `{base_url}/{org}/{project}/_apis/...`  
**And** org must always appear before project in the URL path  
**And** this applies even when collection is already in base_url (on-premise)

**Example URLs**:
- Cloud: `https://dev.azure.com/myorg/myproject/_apis/wit/wiql?api-version=7.1`
- On-premise: `https://server/myorg/myproject/_apis/wit/wiql?api-version=7.1`

### Requirement: Azure DevOps Status Mapping and Configuration

The system SHALL support configurable mapping between OpenSpec statuses and ADO work item states, with defaults aligned to backlog adapter patterns.

#### Scenario: Default status mapping

- **WHEN** OpenSpec status is "proposed"
- **THEN** ADO state maps to "New"
- **WHEN** OpenSpec status is "in-progress"
- **THEN** ADO state maps to "Active"
- **WHEN** OpenSpec status is "applied"
- **THEN** ADO state maps to "Closed"
- **WHEN** OpenSpec status is "deprecated"
- **THEN** ADO state maps to "Removed"
- **WHEN** OpenSpec status is "discarded"
- **THEN** ADO state maps to "Rejected"

#### Scenario: Override status mapping

- **WHEN** a custom mapping is provided via configuration
- **THEN** the adapter uses the configured mapping instead of defaults

#### Scenario: Cross-repo support

- **WHEN** `bridge_config.external_base_path` is set
- **THEN** ADO adapter uses the external path for OpenSpec reads and writes

### Requirement: Azure DevOps Work Item Type Defaults

The system SHALL derive the default ADO work item type from the process template (Scrum/Kanban/Agile) and allow explicit overrides.

#### Scenario: Derive work item type from Scrum template

- **WHEN** the ADO process template is Scrum
- **THEN** the default work item type is "Product Backlog Item"

#### Scenario: Derive work item type from Agile template

- **WHEN** the ADO process template is Agile
- **THEN** the default work item type is "User Story"

#### Scenario: Derive work item type from Kanban workflow

- **WHEN** the ADO process template is Kanban
- **THEN** the default work item type is "User Story"

#### Scenario: Override work item type

- **WHEN** an explicit work item type is provided via configuration
- **THEN** the adapter uses the configured work item type

### Requirement: Token Refresh with Persistent Cache

The ADO adapter SHALL support automatic OAuth token refresh using persistent token cache, similar to Azure CLI behavior. OAuth tokens expire after ~1 hour, and automatic refresh using persistent cache allows seamless operation without frequent re-authentication, improving user experience.

#### Scenario: Automatic Token Refresh on Expiration

**Given** an ADO adapter with an expired OAuth token  
**And** a valid refresh token exists in persistent cache  
**When** the adapter detects the token is expired  
**Then** the adapter must automatically refresh the token using the cached refresh token  
**And** the adapter must update the stored access token  
**And** the operation must continue without user interaction  
**And** debug output should indicate token refresh occurred

#### Scenario: Token Refresh Failure Handling

**Given** an ADO adapter with an expired OAuth token  
**And** no valid refresh token exists in persistent cache (or refresh token expired)  
**When** the adapter attempts to refresh the token  
**Then** the adapter must provide helpful error messages  
**And** the error message must suggest using PAT for longer-lived tokens  
**And** the error message must suggest re-authentication via `specfact auth azure-devops`

### Requirement: Backlog Adapter Bulk Fetching Methods

The system SHALL extend `BacklogAdapterMixin` with abstract methods for bulk fetching backlog items and relationships to support dependency graph analysis.

#### Scenario: Implement bulk fetching in adapters

- **GIVEN** `BacklogAdapterMixin` is extended with abstract methods for bulk fetching
- **WHEN** a backlog adapter (GitHub, ADO) implements `BacklogAdapterMixin`
- **THEN** adapter must implement `fetch_all_issues(project_id: str, filters: dict | None = None) -> list[dict[str, Any]]` abstract method
- **AND** adapter must implement `fetch_relationships(project_id: str) -> list[dict[str, Any]]` abstract method
- **AND** `GitHubAdapter` implements `fetch_all_issues()` using GitHub API to fetch all issues from repository
- **AND** `GitHubAdapter` implements `fetch_relationships()` using GitHub API to fetch issue links and dependencies
- **AND** `AdoAdapter` implements `fetch_all_issues()` using ADO API to fetch all work items from project
- **AND** `AdoAdapter` implements `fetch_relationships()` using ADO API to fetch work item relations

### Requirement: Backlog Adapter Integration with Dependency Graph

The system SHALL support using backlog adapters (GitHub, ADO, Jira) to fetch raw backlog items and relationships for dependency graph analysis.

#### Scenario: Fetch backlog items for graph building

- **GIVEN** a backlog adapter (GitHub, ADO) is configured
- **WHEN** `BacklogGraphBuilder` needs to build a dependency graph
- **THEN** adapter's `fetch_all_issues(project_id: str, filters: dict | None = None) -> list[dict[str, Any]]` method is called to get all raw items
- **AND** adapter's `fetch_relationships(project_id: str) -> list[dict[str, Any]]` method is called to get all raw relationships
- **AND** raw data is passed to `BacklogGraphBuilder.add_items()` and `BacklogGraphBuilder.add_dependencies()`
- **AND** adapter-specific data is preserved in `BacklogItem.raw_data` field

#### Scenario: BacklogAdapterMixin extends with bulk fetching methods

- **GIVEN** `BacklogAdapterMixin` is extended with abstract methods for bulk fetching
- **WHEN** a backlog adapter (GitHub, ADO) implements `BacklogAdapterMixin`
- **THEN** adapter must implement `fetch_all_issues(project_id: str, filters: dict | None = None) -> list[dict[str, Any]]` abstract method
- **AND** adapter must implement `fetch_relationships(project_id: str) -> list[dict[str, Any]]` abstract method
- **AND** `GitHubAdapter` implements `fetch_all_issues()` using GitHub API to fetch all issues from repository
- **AND** `GitHubAdapter` implements `fetch_relationships()` using GitHub API to fetch issue links and dependencies
- **AND** `AdoAdapter` implements `fetch_all_issues()` using ADO API to fetch all work items from project
- **AND** `AdoAdapter` implements `fetch_relationships()` using ADO API to fetch work item relations

#### Scenario: Use adapter registry for graph building

- **GIVEN** backlog dependency analysis commands need to fetch data
- **WHEN** `specfact backlog analyze-deps --adapter github --project-id owner/repo` is executed
- **THEN** `AdapterRegistry.get_adapter("github")` is used to retrieve GitHub adapter
- **AND** adapter's `fetch_all_issues(project_id)` and `fetch_relationships(project_id)` methods are called
- **AND** no hard-coded adapter checks are used in graph building logic
- **AND** adapter methods return lists of dicts with raw provider data

#### Scenario: Support cross-adapter graph analysis

- **GIVEN** backlog items exist in multiple providers (GitHub and ADO)
- **WHEN** dependency analysis is performed across providers
- **THEN** each provider's adapter is used to fetch items
- **AND** items from different providers are unified into single `BacklogGraph`
- **AND** provider information is preserved in `BacklogItem.raw_data` and `BacklogGraph.provider`

### Requirement: Template-Driven Mapping for Adapters

The system SHALL support provider-specific templates for mapping adapter data to unified dependency graph model.

#### Scenario: Use ADO template for ADO adapter

- **GIVEN** ADO adapter is used with `--template ado_scrum`
- **WHEN** `BacklogGraphBuilder` processes ADO work items
- **THEN** ADO-specific template rules are applied (WorkItemType → ItemType mapping, relation types → DependencyType mapping)
- **AND** ADO state values are mapped to normalized status values
- **AND** ADO-specific fields are preserved in `raw_data`

#### Scenario: Use GitHub template for GitHub adapter

- **GIVEN** GitHub adapter is used with `--template github_projects`
- **WHEN** `BacklogGraphBuilder` processes GitHub issues
- **THEN** GitHub-specific template rules are applied (labels → ItemType mapping, linked issues → DependencyType mapping)
- **AND** GitHub state values are mapped to normalized status values
- **AND** GitHub-specific fields are preserved in `raw_data`

#### Scenario: Custom template overrides adapter defaults

- **GIVEN** a user provides custom YAML config with type mapping overrides
- **WHEN** `BacklogGraphBuilder` is initialized with custom config
- **THEN** custom rules override template rules
- **AND** adapter-specific data is still accessible via `raw_data`
- **AND** unified graph model is used regardless of adapter

