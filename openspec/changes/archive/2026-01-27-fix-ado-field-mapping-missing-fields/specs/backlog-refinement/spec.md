# backlog-refinement Specification

## MODIFIED Requirements

### Requirement: Abstract Field Mapping Layer

The system SHALL provide an abstract field mapping layer that normalizes provider-specific field structures to canonical field names.

#### Scenario: ADO field extraction from separate fields

- **GIVEN** an ADO work item with `System.Description`, `System.AcceptanceCriteria`, `Microsoft.VSTS.Common.AcceptanceCriteria`, and `Microsoft.VSTS.Common.StoryPoints` fields
- **WHEN** `AdoFieldMapper` extracts fields
- **THEN** the `description` field is populated from `System.Description`
- **AND** the `acceptance_criteria` field is populated from either `System.AcceptanceCriteria` or `Microsoft.VSTS.Common.AcceptanceCriteria` (checks all alternatives and uses first found value)
- **AND** the `story_points` field is populated from `Microsoft.VSTS.Common.StoryPoints`
- **AND** when writing updates back to ADO, the system prefers `System.*` fields over `Microsoft.VSTS.Common.*` fields for better Scrum template compatibility

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

## ADDED Requirements

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
