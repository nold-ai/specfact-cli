# backlog-refinement Specification

## Purpose
TBD - created by archiving change add-template-driven-backlog-refinement. Update Purpose after archive.
## Requirements
### Requirement: Backlog Item Refinement Command

The system SHALL provide a `specfact backlog refine` command that enables teams to standardize backlog items using AI-assisted template matching and refinement.

#### Scenario: Display assignee and acceptance criteria in preview output

- **GIVEN** a backlog item with `assignees: ["John Doe"]` and `acceptance_criteria: "User can login"`
- **WHEN** preview mode is displayed (`specfact backlog refine --preview`)
- **THEN** the output should show `[bold]Assignee:[/bold] John Doe` after the Provider field
- **AND** the output should show `[bold]Acceptance Criteria:[/bold]` with the acceptance criteria content
- **AND** if acceptance criteria is required by the template but empty, it should show `(empty - required field)` indicator
- **AND** if assignees list is empty, it should show `[bold]Assignee:[/bold] Unassigned`
- **AND** required fields from the template are always displayed, even when empty, to help copilot identify missing elements
- **AND** the assignee should be displayed before Story Metrics section

### Requirement: Backlog Item Domain Model

The system SHALL provide a unified `BacklogItem` domain model that represents backlog items from any provider (GitHub, ADO, JIRA, etc.) with lossless data preservation.

#### Scenario: BacklogItem creation from GitHub issue

- **WHEN** a GitHub issue is fetched via adapter
- **THEN** the system creates a `BacklogItem` with normalized fields (title, body_markdown, state) and preserves provider-specific data in `provider_fields`

#### Scenario: Lossless round-trip preservation

- **WHEN** a `BacklogItem` is created from a provider and then updated back to the provider
- **THEN** all original provider-specific data is preserved via `provider_fields`, ensuring zero data loss

#### Scenario: Refinement state tracking

- **WHEN** a backlog item is refined
- **THEN** the system records `detected_template`, `template_confidence`, `refined_body`, `refinement_applied`, and `refinement_timestamp` in the item

#### Scenario: Sprint and release tracking

- **WHEN** a backlog item is created from a provider (ADO, GitHub, Jira)
- **THEN** the system extracts and normalizes sprint and release information into `sprint` and `release` fields, preserving original provider format in `provider_fields`

### Requirement: Template Registry Management

The system SHALL provide a template registry that manages backlog templates with detection, matching, and scoping capabilities.

#### Scenario: Register corporate template

- **WHEN** a template is registered with scope "corporate"
- **THEN** the template is available to all teams and projects

#### Scenario: Register team-specific template

- **WHEN** a template is registered with scope "team" and team_id
- **THEN** the template is only available to that specific team

#### Scenario: List available templates

- **WHEN** a user queries the template registry
- **THEN** the system returns all templates matching the requested scope (corporate, team, or user)

#### Scenario: Persona-specific template selection

- **WHEN** a template is registered with `personas: ["product-owner"]`
- **THEN** the template is only used when `--persona product-owner` is specified or when resolving templates for product-owner workflows

#### Scenario: Framework-specific template selection

- **WHEN** a template is registered with `framework: "scrum"`
- **THEN** the template is only used when `--framework scrum` is specified or when resolving templates for Scrum workflows

#### Scenario: Provider-specific template selection

- **WHEN** a template is registered with `provider: "ado"`
- **THEN** the template is prioritized when refining items from Azure DevOps adapter

#### Scenario: Priority-based template resolution

- **WHEN** multiple templates match (provider+framework+persona, framework+persona, framework, default)
- **THEN** the system selects the most specific match (provider+framework+persona) and falls back to less specific matches if not found

### Requirement: Abstract Field Mapping Layer

The system SHALL provide an abstract field mapping layer that normalizes provider-specific field structures to canonical field names.

#### Scenario: ADO field extraction from separate fields

- **GIVEN** an ADO work item with `System.Description`, `System.AcceptanceCriteria`, `Microsoft.VSTS.Common.AcceptanceCriteria`, and `Microsoft.VSTS.Common.StoryPoints` fields
- **WHEN** `AdoFieldMapper` extracts fields
- **THEN** the `description` field is populated from `System.Description`
- **AND** the `acceptance_criteria` field is populated from either `System.AcceptanceCriteria` or `Microsoft.VSTS.Common.AcceptanceCriteria` (checks all alternatives and uses first found value)
- **AND** the `story_points` field is populated from `Microsoft.VSTS.Common.StoryPoints`
- **AND** when writing updates back to ADO, the system prefers `System.*` fields over `Microsoft.VSTS.Common.*` fields for better Scrum template compatibility

### Requirement: Enhanced BacklogItem Model

The system SHALL extend the `BacklogItem` model with story points, business value, priority, and acceptance criteria fields.

#### Scenario: BacklogItem with story points

- **GIVEN** a backlog item is created from an ADO work item with `Microsoft.VSTS.Common.StoryPoints = 8`
- **WHEN** the item is converted to `BacklogItem`
- **THEN** the `story_points` field is set to `8`
- **AND** the value is preserved in `provider_fields` for round-trip sync

#### Scenario: BacklogItem with business value and priority

- **GIVEN** a backlog item is created from an ADO work item with `Microsoft.VSTS.Common.BusinessValue = 5` and `Microsoft.VSTS.Common.Priority = 2`
- **WHEN** the item is converted to `BacklogItem`
- **THEN** the `business_value` field is set to `5`
- **AND** the `priority` field is set to `2`
- **AND** both values are preserved in `provider_fields`

### Requirement: Provider-Aware Validation

The system SHALL validate backlog item refinement differently based on the provider (GitHub vs ADO).

#### Scenario: GitHub validation checks markdown headings

- **GIVEN** a GitHub backlog item with body containing `## Acceptance Criteria` heading
- **AND** the template requires "Acceptance Criteria" section
- **WHEN** refinement validation is performed
- **THEN** the validation checks for the markdown heading in `body_markdown`
- **AND** validation passes if the heading exists

#### Scenario: ADO validation checks separate fields

- **GIVEN** an ADO backlog item with `System.AcceptanceCriteria` field populated
- **AND** the template requires "Acceptance Criteria" section
- **WHEN** refinement validation is performed
- **THEN** the validation checks for the `acceptance_criteria` field (not a heading in body)
- **AND** validation passes if the field exists and is non-empty

### Requirement: Story Complexity Analysis

The system SHALL calculate story complexity scores and detect stories that need splitting.

#### Scenario: Story points complexity calculation

- **GIVEN** a backlog item with `story_points = 13` and `business_value = 8`
- **WHEN** complexity score is calculated
- **THEN** the score considers both story points and business value
- **AND** stories > 13 points are flagged for potential splitting

#### Scenario: Multi-sprint story detection

- **GIVEN** a backlog item with `story_points = 21` (exceeds single sprint capacity)
- **OR** a backlog item spanning multiple iterations
- **WHEN** story splitting detection is performed
- **THEN** the system suggests splitting into multiple stories under the same feature
- **AND** provides rationale for the splitting suggestion

#### Scenario: Story splitting suggestion in refinement output

- **GIVEN** a backlog item refinement session with a complex story (story_points > 13)
- **WHEN** refinement completes
- **THEN** the output includes a story splitting suggestion
- **AND** the suggestion includes recommended split points and rationale

### Requirement: Custom Template Field Mapping

The system SHALL support custom ADO field mappings via YAML configuration files.

#### Scenario: Load custom field mapping

- **GIVEN** a custom mapping file `.specfact/templates/backlog/field_mappings/ado_custom.yaml` exists
- **WHEN** `AdoFieldMapper` is initialized
- **THEN** the custom mapping is loaded and merged with defaults
- **AND** custom mappings override default mappings for the same canonical field

#### Scenario: Fallback to default mapping

- **GIVEN** no custom mapping file exists
- **WHEN** `AdoFieldMapper` is initialized
- **THEN** default mappings are used (e.g., `Microsoft.VSTS.Common.StoryPoints` → `story_points`)
- **AND** the mapper works correctly with default mappings

#### Scenario: Custom mapping via CLI option

- **GIVEN** a user runs `specfact backlog refine --custom-field-mapping /path/to/custom.yaml`
- **WHEN** the command executes
- **THEN** the custom mapping file is loaded and used for field extraction
- **AND** validation errors are shown if the mapping file is invalid

### Requirement: Agile Framework Alignment (Kanban/Scrum/SAFe)

The system SHALL support field mapping and validation aligned with Kanban, Scrum, and SAFe agile frameworks.

#### Scenario: Scrum field mapping

- **GIVEN** an ADO work item using Scrum process template
- **WHEN** fields are extracted using `AdoFieldMapper`
- **THEN** work item type is mapped (Product Backlog Item, Bug, Task, etc.)
- **AND** story points are extracted from `Microsoft.VSTS.Scheduling.StoryPoints`
- **AND** sprint/iteration information is extracted from `System.IterationPath`
- **AND** priority is extracted from `Microsoft.VSTS.Common.Priority`

#### Scenario: SAFe field mapping

- **GIVEN** an ADO work item using SAFe process template
- **WHEN** fields are extracted using `AdoFieldMapper`
- **THEN** work item type is mapped (Epic, Feature, User Story, Task, Bug, etc.)
- **AND** value points are extracted from `Microsoft.VSTS.Common.ValueArea` or custom SAFe fields
- **AND** story points are extracted from `Microsoft.VSTS.Scheduling.StoryPoints`
- **AND** business value is extracted from `Microsoft.VSTS.Common.BusinessValue`
- **AND** Epic → Feature → Story hierarchy is preserved via parent relationships

#### Scenario: Kanban field mapping

- **GIVEN** a GitHub issue or ADO work item using Kanban workflow
- **WHEN** fields are extracted
- **THEN** work item type is mapped (User Story, Task, Bug, etc.)
- **AND** state/status is mapped to Kanban columns (Backlog, In Progress, Done, etc.)
- **AND** priority is extracted for Kanban prioritization
- **AND** no sprint/iteration information is required (Kanban doesn't use sprints)

#### Scenario: SAFe Value Points calculation

- **GIVEN** a SAFe Feature or User Story with business value and story points
- **WHEN** value points are calculated
- **THEN** value points = business_value / story_points (or SAFe-specific formula)
- **AND** value points are used for WSJF (Weighted Shortest Job First) prioritization
- **AND** value points are stored in `value_points` field

#### Scenario: Work item type hierarchy validation (SAFe)

- **GIVEN** a backlog item with `work_item_type = "User Story"`
- **AND** the item has a parent with `work_item_type = "Feature"`
- **AND** the feature has a parent with `work_item_type = "Epic"`
- **WHEN** SAFe hierarchy validation is performed
- **THEN** the hierarchy is validated (Epic → Feature → Story → Task)
- **AND** validation errors are reported if hierarchy is invalid (e.g., Story without Feature parent)

#### Scenario: Definition of Ready (DoR) per framework

- **GIVEN** a backlog item refinement session with DoR rules enabled
- **AND** the framework is Scrum (requires story_points, acceptance_criteria)
- **WHEN** DoR validation is performed
- **THEN** Scrum-specific DoR rules are checked (story_points required, acceptance_criteria required)
- **AND** validation passes only if all Scrum DoR rules are satisfied

- **GIVEN** a backlog item refinement session with DoR rules enabled
- **AND** the framework is SAFe (requires value_points, story_points, acceptance_criteria, parent Feature)
- **WHEN** DoR validation is performed
- **THEN** SAFe-specific DoR rules are checked (value_points required, parent Feature required)
- **AND** validation passes only if all SAFe DoR rules are satisfied

- **GIVEN** a backlog item refinement session with DoR rules enabled
- **AND** the framework is Kanban (requires priority, acceptance_criteria, no sprint requirement)
- **WHEN** DoR validation is performed
- **THEN** Kanban-specific DoR rules are checked (priority required, no story_points requirement)
- **AND** validation passes only if all Kanban DoR rules are satisfied

### Requirement: Interactive Template Mapping Command

The system SHALL provide an interactive command to discover and map ADO fields to canonical field names.

#### Scenario: Discover Available ADO Fields

- **GIVEN** a user wants to map custom ADO fields
- **WHEN** the user runs `specfact backlog map-fields --ado-org myorg --ado-project myproject --ado-token <token>`
- **THEN** the command should fetch available fields from ADO API (`GET https://dev.azure.com/{org}/{project}/_apis/wit/fields`)
- **AND** the command should filter out system-only fields (e.g., `System.Id`, `System.Rev`)
- **AND** the command should display relevant fields for mapping

#### Scenario: Map ADO Fields Interactively

- **GIVEN** an interactive mapping session is active
- **WHEN** the user selects a canonical field (e.g., `acceptance_criteria`)
- **THEN** the command should pre-populate with default mappings from `AdoFieldMapper.DEFAULT_FIELD_MAPPINGS` (checking which exist in fetched fields)
- **AND** the command should prefer `Microsoft.VSTS.Common.*` fields over `System.*` fields for better compatibility
- **AND** the command should use regex/fuzzy matching to suggest potential matches when no default mapping exists
- **AND** the command should show current mapping (if exists from custom mapping) or default mapping or "<no mapping>"
- **AND** the command should display all available ADO fields in scrollable interactive menu with arrow key navigation (↑↓ to navigate, ⏎ to select)
- **AND** the user can select an ADO field or "<no mapping>" option
- **AND** the best match should be pre-selected (existing > default > fuzzy match > "<no mapping>")
- **AND** the selection should be saved for the current canonical field

#### Scenario: Reset Custom Mappings

- **GIVEN** a user has created custom field mappings in `.specfact/templates/backlog/field_mappings/ado_custom.yaml`
- **WHEN** the user runs `specfact backlog map-fields --ado-org myorg --ado-project myproject --reset`
- **THEN** the custom mapping file should be deleted
- **AND** the command should display success message: "Reset custom field mapping (deleted ...)"
- **AND** default mappings from `AdoFieldMapper.DEFAULT_FIELD_MAPPINGS` will be used on next run
- **AND** the command should return early (no need to fetch fields or do interactive mapping)

#### Scenario: Token Resolution for Interactive Mapping

- **GIVEN** a user wants to run `specfact backlog map-fields` without providing `--ado-token`
- **WHEN** the command executes
- **THEN** the command should resolve token in order: explicit token > env var > stored token (non-expired) > expired stored token (with warning)
- **AND** the command should support both Bearer (OAuth) and Basic (PAT) authentication schemes
- **AND** if no token is found, the command should display helpful error message with options

#### Scenario: Save Per-Project Mapping

- **GIVEN** a user completes interactive mapping for all canonical fields
- **WHEN** the mapping is saved
- **THEN** the mapping should be saved to `.specfact/templates/backlog/field_mappings/ado_custom.yaml`
- **AND** the mapping should follow `FieldMappingConfig` schema
- **AND** the mapping should be validated before saving
- **AND** the command should display success message with file path

#### Scenario: Validate Mapping Before Saving

- **GIVEN** a user has selected mappings for canonical fields
- **WHEN** the user attempts to save the mapping
- **THEN** the command should validate:
  - No duplicate ADO field mappings (same ADO field mapped to multiple canonical fields)
  - Required canonical fields are mapped (if applicable)
  - YAML syntax is valid
- **AND** if validation fails, the command should display errors and allow correction
- **AND** if validation passes, the mapping should be saved

### Requirement: Template Initialization in specfact init

The system SHALL copy default ADO field mapping templates to `.specfact/templates/backlog/field_mappings/` during `specfact init`.

#### Scenario: Initialize Templates During Init

- **GIVEN** a user runs `specfact init` in a project directory
- **WHEN** the command completes
- **THEN** the directory `.specfact/templates/backlog/field_mappings/` should be created
- **AND** default templates (`ado_default.yaml`, `ado_scrum.yaml`, `ado_agile.yaml`, `ado_safe.yaml`, `ado_kanban.yaml`) should be copied
- **AND** users can review and modify templates directly in their project

#### Scenario: Skip Template Copying if Files Exist

- **GIVEN** `.specfact/templates/backlog/field_mappings/ado_default.yaml` already exists
- **WHEN** the user runs `specfact init`
- **THEN** the existing file should not be overwritten (unless `--force` flag is used)
- **AND** the command should display a message indicating templates already exist

#### Scenario: Force Overwrite Templates

- **GIVEN** `.specfact/templates/backlog/field_mappings/ado_default.yaml` already exists
- **WHEN** the user runs `specfact init --force`
- **THEN** the existing file should be overwritten with the default template
- **AND** the command should display a message indicating templates were overwritten

### Requirement: Progress Indicators for Backlog Refinement Initialization

The system SHALL provide progress feedback during initialization of the `specfact backlog refine` command.

#### Scenario: Display Initialization Progress

- **GIVEN** a user runs `specfact backlog refine` command
- **WHEN** the command starts initialization (before "Fetching backlog items" message)
- **THEN** the command should display progress indicators for:
  - Template initialization (loading built-in and custom templates)
  - Template detector initialization
  - AI refiner initialization
  - Adapter initialization
  - DoR configuration loading (if `--check-dor` flag is set)
  - Configuration validation
- **AND** each step should show a spinner and update to checkmark when complete
- **AND** the progress should use Rich Progress with time elapsed column
- **AND** this provides user feedback during 5-10 second initialization delay (especially important in corporate environments with security scans/firewalls)

