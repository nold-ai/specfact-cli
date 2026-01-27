# backlog-refinement Specification

## Purpose

This specification defines requirements for backlog item refinement with proper field mapping, provider-aware validation, and story complexity analysis.

## ADDED Requirements

### Requirement: Abstract Field Mapping Layer

The system SHALL provide an abstract field mapping layer that normalizes provider-specific field structures to canonical field names.

#### Scenario: GitHub field extraction from markdown body

- **GIVEN** a GitHub issue with markdown body containing `## Acceptance Criteria` section
- **WHEN** `GitHubFieldMapper` extracts fields
- **THEN** the `acceptance_criteria` field is populated from the markdown heading content
- **AND** the `description` field is populated from the default body content or `## Description` section

#### Scenario: ADO field extraction from separate fields

- **GIVEN** an ADO work item with `System.Description`, `System.AcceptanceCriteria`, and `Microsoft.VSTS.Common.StoryPoints` fields
- **WHEN** `AdoFieldMapper` extracts fields
- **THEN** the `description` field is populated from `System.Description`
- **AND** the `acceptance_criteria` field is populated from `System.AcceptanceCriteria`
- **AND** the `story_points` field is populated from `Microsoft.VSTS.Common.StoryPoints`

#### Scenario: Custom ADO field mapping

- **GIVEN** a custom ADO template with field `Custom.StoryPoints` instead of `Microsoft.VSTS.Common.StoryPoints`
- **AND** a custom mapping file `.specfact/templates/backlog/field_mappings/ado_custom.yaml` specifies the mapping
- **WHEN** `AdoFieldMapper` extracts fields
- **THEN** the `story_points` field is populated from `Custom.StoryPoints` using the custom mapping
- **AND** other fields use default mappings if not overridden

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
