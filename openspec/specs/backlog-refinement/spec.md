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

### Requirement: Import refined content from temporary file

The system SHALL support importing refined backlog content from a temporary markdown file (same format as export) when `specfact backlog refine --import-from-tmp` is used, matching items by ID and updating remote backlog via the adapter when `--write` is set.

#### Scenario: Import refined content from temporary file

- **GIVEN** a markdown file in the same format as the export from `specfact backlog refine --export-to-tmp` (header, then per-item blocks with `## Item N:`, **ID**, **Body** in ```markdown ...```, **Acceptance Criteria**)
- **AND** the user runs `specfact backlog refine --import-from-tmp --tmp-file <path>` with the same adapter and filters as used for export (so the same set of items is fetched)
- **WHEN** the import file exists and is readable
- **THEN** the system parses the file and matches each block to a fetched item by **ID**
- **AND** for each matched item the system updates `body_markdown` and `acceptance_criteria` (and optionally title/metrics) from the parsed block
- **AND** if `--write` is not set, the system prints a preview (e.g. "Would update N items") and does not call the adapter
- **AND** if `--write` is set, the system calls `adapter.update_backlog_item(item, update_fields=[...])` for each updated item and prints a success summary (e.g. "Updated N backlog items")
- **AND** the system does not show "Import functionality pending implementation"

#### Scenario: Import file not found

- **GIVEN** the user runs `specfact backlog refine --import-from-tmp` (or with `--tmp-file <path>`)
- **WHEN** the resolved import file does not exist
- **THEN** the system prints an error with the expected path and suggests using `--tmp-file` to specify the path
- **AND** the command exits with non-zero status

### Requirement: Ignore Already-Refined Items by Default

The system SHALL support `--ignore-refined` (default) and `--no-ignore-refined` so that when `--limit N` is used, the limit applies to items that need refinement (already-refined items are excluded from the batch by default).

#### Scenario: Limit applies to items needing refinement when ignore-refined

- **GIVEN** the user runs `specfact backlog refine <adapter> --limit 3` (default `--ignore-refined`)
- **AND** the adapter returns at least 5 items, of which the first 3 are already refined (checkboxes + all required sections or high confidence with no missing fields)
- **WHEN** the command processes items
- **THEN** the system filters out already-refined items, then takes the first 3 that need refinement
- **AND** the user sees up to 3 items that actually require refinement (no loop of the same 3 refined items)

#### Scenario: No-ignore-refined preserves previous behavior

- **GIVEN** the user runs `specfact backlog refine <adapter> --limit 3 --no-ignore-refined`
- **WHEN** the command processes items
- **THEN** the system takes the first 3 items from the fetch and processes them in order
- **AND** already-refined items are skipped in the loop (current behavior)

### Requirement: Focused Refinement by Issue ID

The system SHALL support `--id ISSUE_ID` to refine only the backlog item with the given issue or work item ID.

#### Scenario: Refine single item by ID

- **GIVEN** the user runs `specfact backlog refine <adapter> --id 123` (with required adapter options)
- **WHEN** the adapter returns items including item with id 123
- **THEN** the system filters to only the item with id 123 and refines only that item
- **AND** other items are not processed

#### Scenario: ID not found

- **GIVEN** the user runs `specfact backlog refine <adapter> --id 999` (with required adapter options)
- **WHEN** no item with id 999 is in the fetched set
- **THEN** the system prints a clear error (e.g. "No backlog item with id 999 found") and exits with non-zero status

### Requirement: Export refine context includes comments without truncation by default

The system SHALL include issue/work item comments in `specfact backlog refine --export-to-tmp` output so exported refinement context is complete by default. Comment content SHALL not be truncated unless explicitly requested by the user.

**Rationale**: Refinement quality depends on full historical discussion context, especially for ADO work items where key decisions are often in comments.

#### Scenario: Refine export contains full comments by default

**Given**: The user runs `specfact backlog refine --export-to-tmp` for an adapter that supports comments

**And**: A backlog item has comments in the provider

**When**: No explicit comment-window options are provided

**Then**: The exported markdown includes all comments for the item

**And**: Comment text is preserved without truncation

#### Scenario: Refine export includes copilot instruction block

**Given**: The user runs `specfact backlog refine --export-to-tmp`

**When**: The export file is generated

**Then**: The file starts with a clear copilot instruction/prompt block before item entries

**And**: The instruction block tells the user/copilot how to process item sections consistently

**And**: The instruction block explicitly states that the refined artifact for import must omit the instruction block and contain only item sections

#### Scenario: Refine export instructions match interactive refinement rules

**Given**: The user runs `specfact backlog refine --export-to-tmp`

**When**: Copilot reads the exported file

**Then**: The exported instruction block includes the same refinement rules used in interactive mode (preserve scope, required-section completion, ambiguity notes, provider-aware formatting)

**And**: Each item includes template guidance (target template, required sections, optional sections) so export processing can follow the same structure as interactive prompts

### Requirement: Refine preview includes scoped comment context

The system SHALL include issue/work item comments in `specfact backlog refine --preview` output with a scoped default to keep terminal output readable.

**Rationale**: Refinement decisions depend on discussion history, but preview output must stay concise for day-to-day CLI usage.

#### Scenario: Refine preview shows last two comments by default

**Given**: The user runs `specfact backlog refine --preview` for an adapter that supports comments

**And**: A backlog item has multiple comments

**When**: No explicit comment-window options are provided

**Then**: The preview shows the two newest comments for that item

#### Scenario: First-comments limit on refine preview

**Given**: The user runs `specfact backlog refine --preview --first-comments 5`

**When**: A backlog item has more than five comments

**Then**: The preview comment section contains only the first five comments for that item

#### Scenario: Last-comments limit on refine preview

**Given**: The user runs `specfact backlog refine --preview --last-comments 4`

**When**: A backlog item has more than four comments

**Then**: The preview comment section contains only the last four comments for that item

#### Scenario: Preview shows comment-fetch progress for large batches

**Given**: The user runs `specfact backlog refine --preview` for many backlog items

**When**: The command fetches comments across adapters

**Then**: The CLI shows progress feedback with item position (for example `Fetching issue n/m ...`) until comment fetch completes

#### Scenario: Preview comment output is clearly scoped

**Given**: The preview includes comments for an item

**When**: The command renders preview detail

**Then**: Each comment is rendered in a clearly scoped block-style container so users can distinguish comment boundaries from body/metadata

#### Scenario: Preview indicates when no comments exist

**Given**: The preview fetches comments for an item

**When**: No comments are available for that issue/work item

**Then**: The preview still shows a comments section with an explicit "no comments found" hint

**Acceptance Criteria**:

- Default refine preview includes the last two comments per item.
- Limits are optional and deterministic for preview output.
- If both first and last limits are provided, command fails with a clear validation error.
- `--export-to-tmp` always includes full comments, independent of preview comment-window options.
- Preview provides visible comment-fetch progress for multi-item runs.
- Preview comment rendering uses block-style formatting to make comment boundaries explicit.
- Preview explicitly indicates when an item has no comments.

### Requirement: Refine write prompts include comment context

The system SHALL include issue/work item comments in generated refinement prompts during `specfact backlog refine --write` so AI-assisted refinement reflects the latest discussion state.

**Rationale**: Comment threads are the living source of truth; prompt context must include them to avoid refining against stale issue bodies.

#### Scenario: Write-mode prompt includes full comments by default

**Given**: The user runs `specfact backlog refine --write`

**And**: The selected issue/work item has comments

**When**: No explicit comment-window options are provided

**Then**: The generated refinement prompt includes all available comments for that item

#### Scenario: Write-mode prompt applies comment-window options

**Given**: The user runs `specfact backlog refine --write --last-comments 5`

**When**: The item has more than five comments

**Then**: The generated refinement prompt includes only the configured comment window

### Requirement: Refine supports first/last issue windowing

The system SHALL support optional issue window controls for `specfact backlog refine` so users can process the first or last subset of currently filtered backlog items.

**Rationale**: Teams often need a deterministic window over a larger result set (for example oldest/newest slice) without re-running broad filters manually.

#### Scenario: First-issues limit on refine

**Given**: The user runs `specfact backlog refine --first-issues 10`

**When**: More than ten items match after filters/refinement eligibility rules

**Then**: The command sorts items by issue/work-item number ascending and processes only the first ten (lowest IDs / oldest)

#### Scenario: Last-issues limit on refine

**Given**: The user runs `specfact backlog refine --last-issues 10`

**When**: More than ten items match after filters/refinement eligibility rules

**Then**: The command sorts items by issue/work-item number ascending and processes only the last ten (highest IDs / newest)

#### Scenario: First/last issues flags are mutually exclusive

**Given**: The user runs `specfact backlog refine --first-issues 5 --last-issues 5`

**When**: The command validates options

**Then**: The command exits with a clear validation error

### Requirement: ADO comments are fetched from dedicated comments API

For Azure DevOps, the system SHALL fetch work item comments via the dedicated comments endpoint and handle comment pagination to collect complete history.

**Rationale**: ADO work item retrieval and comments retrieval are separate API resources and versions.

#### Scenario: ADO comment pagination retrieves complete history

**Given**: An ADO work item has comments spanning multiple comment pages

**When**: The adapter fetches comments for refine or daily context

**Then**: The adapter calls the ADO comments API and follows continuation tokens until complete

**And**: All comments are returned in stable order for downstream rendering/export

### Requirement: AI Refinement Writeback Preserves Provider Field Semantics

The system SHALL parse structured refinement output into canonical fields before provider writeback so provider-specific fields are updated correctly rather than storing prompt labels verbatim in description/body.

#### Scenario: ADO writeback splits label-style refined output into canonical fields

- **GIVEN** a user runs `specfact backlog refine ado --write`
- **AND** the refined output uses label-style sections such as `Description:`, `Acceptance Criteria:`, `Story Points:`, `Business Value:`, and `Priority:`
- **WHEN** the refinement is accepted
- **THEN** SpecFact parses those sections into canonical fields
- **AND** writes `description` content to ADO description field
- **AND** writes `acceptance_criteria`, `story_points`, `business_value`, and `priority` to their mapped ADO fields when present
- **AND** does not write the entire labeled structure verbatim as ADO description.

#### Scenario: GitHub writeback normalizes label-style refined output to structured markdown

- **GIVEN** a user runs `specfact backlog refine github --write`
- **AND** the refined output uses label-style sections rather than markdown headings
- **WHEN** the refinement is accepted
- **THEN** SpecFact normalizes the output into canonical markdown sections
- **AND** updates issue body and related canonical fields consistently
- **AND** avoids duplicating or flattening structured fields into a single unparsed description block.

#### Scenario: Heading-style narrative sections are preserved during writeback parsing

- **GIVEN** a user runs `specfact backlog refine <provider> --write`
- **AND** the refined output uses markdown headings like `## Notes` and `## Dependencies`
- **WHEN** the refinement output is parsed into canonical fields for writeback
- **THEN** `body_markdown` keeps those narrative sections
- **AND** canonical numeric/provider metadata sections (for example `## Story Points`, `## Business Value`, `## Priority`, `## Provider`) are not duplicated into narrative body text.

#### Scenario: Heading-style narrative sections are matched case-insensitively

- **GIVEN** a user runs `specfact backlog refine <provider> --write`
- **AND** the refined output uses uppercase narrative headings like `## NOTES` and `## DEPENDENCIES`
- **WHEN** the refinement output is parsed into canonical fields for writeback
- **THEN** `body_markdown` preserves those narrative sections as normalized `## Notes` / `## Dependencies` sections
- **AND** writeback does not silently drop narrative context because of heading case differences.

#### Scenario: Label-only field blocks without Description do not leak raw labels into body/description

- **GIVEN** a user runs `specfact backlog refine <provider> --write`
- **AND** the refined output contains label-style field blocks (for example `Acceptance Criteria:`, `Story Points:`, `Priority:`) but no `Description:` block
- **WHEN** the refinement output is parsed into canonical fields for writeback
- **THEN** canonical fields (for example acceptance criteria and numeric fields) are extracted
- **AND** parser fallback does not keep the entire raw labeled payload as `description`
- **AND** `body_markdown` does not contain prompt labels verbatim.

#### Scenario: Mixed heading and inline label formatting preserves description narrative

- **GIVEN** a refined output that uses heading-style sections such as `## Description` and `## Acceptance Criteria`
- **AND** the `## Description` section contains an inline label like `**Notes**:`
- **WHEN** SpecFact parses the refinement output for writeback
- **THEN** text before the inline label in `## Description` is preserved in `body_markdown`
- **AND** label-capture does not swallow subsequent heading sections.

#### Scenario: Prompt format contract includes canonical scaffold and metadata omission rule

- **GIVEN** SpecFact generates a refinement prompt for IDE Copilot
- **WHEN** prompt text is rendered for backlog refine
- **THEN** it includes an explicit expected output scaffold (ordered canonical sections)
- **AND** it instructs Copilot to omit unknown metadata fields (for example area/iteration path) instead of placeholders like "unspecified" or "provide ...".

#### Scenario: Mixed heading description does not duplicate inline notes block

- **GIVEN** a refined output with `## Description` narrative
- **AND** an inline label block like `**Notes**:` appears inside that description section
- **WHEN** SpecFact parses the refinement output for writeback
- **THEN** description narrative is preserved without raw inline label markup
- **AND** notes content appears only once in normalized `## Notes` output.

#### Scenario: Label-style notes preserves internal non-boundary headings

- **GIVEN** a label-style `Notes:` section includes internal headings such as `## Risks`
- **WHEN** SpecFact parses notes/dependencies label blocks
- **THEN** internal headings that are not canonical section boundaries are preserved as notes content
- **AND** parser does not truncate notes at the internal heading line.

#### Scenario: Refine command orchestration remains behaviorally consistent after decomposition

- **GIVEN** `specfact backlog refine` supports initialization, filtering, export/import, interactive refinement, writeback, and summary flows
- **WHEN** the command implementation is decomposed into smaller helper methods
- **THEN** observable CLI behavior and writeback semantics remain unchanged for equivalent inputs
- **AND** command complexity in the top-level `refine` function is reduced to keep the implementation readable and maintainable.

