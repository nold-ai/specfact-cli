## 1. Abstract Field Mapping Layer

- [x] 1.1 Create `FieldMapper` abstract base class
  - [x] 1.1.1 Define canonical field names (description, acceptance_criteria, story_points, business_value, priority, value_points, work_item_type) for Kanban/Scrum/SAFe alignment
  - [x] 1.1.2 Define abstract methods: `extract_fields()`, `map_to_canonical()`, `map_from_canonical()`
  - [x] 1.1.3 Add field mapping registry for provider selection with framework-aware mapping (Kanban, Scrum, SAFe)
  - [x] 1.1.4 Write unit tests for `FieldMapper` base class

- [x] 1.2 Implement `GitHubFieldMapper`
  - [x] 1.2.1 Extract description from body (default content or `## Description` section)
  - [x] 1.2.2 Extract acceptance criteria from `## Acceptance Criteria` heading
  - [x] 1.2.3 Extract story points from `## Story Points` or `**Story Points:**` patterns
  - [x] 1.2.4 Extract business value from `## Business Value` or `**Business Value:**` patterns
  - [x] 1.2.5 Extract priority from `## Priority` or `**Priority:**` patterns
  - [x] 1.2.6 Write unit tests for `GitHubFieldMapper`

- [x] 1.3 Implement `AdoFieldMapper` with default mappings
  - [x] 1.3.1 Extract description from `System.Description` field
  - [x] 1.3.2 Extract acceptance criteria from `System.AcceptanceCriteria` field
  - [x] 1.3.3 Extract story points from `Microsoft.VSTS.Common.StoryPoints` or `Microsoft.VSTS.Scheduling.StoryPoints` field (Scrum/SAFe)
  - [x] 1.3.4 Extract business value from `Microsoft.VSTS.Common.BusinessValue` field
  - [x] 1.3.5 Extract priority from `Microsoft.VSTS.Common.Priority` field
  - [x] 1.3.6 Extract value points from SAFe-specific fields (calculate if needed: business_value / story_points)
  - [x] 1.3.7 Extract work item type from `System.WorkItemType` field (Epic, Feature, User Story, Task, Bug, etc.)
  - [x] 1.3.8 Write unit tests for `AdoFieldMapper` with default mappings (Scrum, SAFe, Kanban)

- [x] 1.4 Add custom template mapping support
  - [x] 1.4.1 Create template configuration schema (`template_config.py`)
  - [x] 1.4.2 Support YAML configuration for custom field mappings
  - [x] 1.4.3 Load custom mappings from `.specfact/templates/backlog/field_mappings/ado_custom.yaml`
  - [x] 1.4.4 Fallback to default mappings if custom mapping not provided
  - [x] 1.4.5 Write unit tests for custom template mapping

## 2. Enhanced BacklogItem Model

- [x] 2.1 Add new fields to `BacklogItem` model
  - [x] 2.1.1 Add `story_points: int | None` field with validation (0-100 range, Scrum/SAFe)
  - [x] 2.1.2 Add `business_value: int | None` field with validation (0-100 range, Scrum/SAFe)
  - [x] 2.1.3 Add `priority: int | None` field with validation (1-4 range, 1=highest, all frameworks)
  - [x] 2.1.4 Add `value_points: int | None` field with validation (SAFe-specific, calculated from business_value / story_points)
  - [x] 2.1.5 Add `acceptance_criteria: str | None` field (separate from body_markdown, all frameworks)
  - [x] 2.1.6 Add `work_item_type: str | None` field (Epic, Feature, User Story, Task, Bug, etc., framework-aware)
  - [x] 2.1.7 Update model docstrings and field descriptions with framework notes
  - [x] 2.1.8 Write unit tests for new fields (Scrum, SAFe, Kanban scenarios)

- [x] 2.2 Update converter to use field mappers
  - [x] 2.2.1 Update `convert_github_issue_to_backlog_item()` to use `GitHubFieldMapper`
  - [x] 2.2.2 Update `convert_ado_work_item_to_backlog_item()` to use `AdoFieldMapper`
  - [x] 2.2.3 Preserve provider-specific fields in `provider_fields` dict
  - [x] 2.2.4 Write integration tests for converter with field mappers

## 3. Provider-Aware Validation

- [x] 3.1 Update `BacklogAIRefiner._validate_required_sections()` to be provider-aware
  - [x] 3.1.1 Detect provider from `BacklogItem.provider` field
  - [x] 3.1.2 For GitHub: Check for markdown headings in `body_markdown` (current behavior)
  - [x] 3.1.3 For ADO: Check for separate fields (not headings in body)
  - [x] 3.1.4 Use field mapper to determine validation strategy
  - [x] 3.1.5 Write unit tests for provider-aware validation

- [x] 3.2 Update refinement prompt generation
  - [x] 3.2.1 Include provider-specific instructions in refinement prompts
  - [x] 3.2.2 For GitHub: Instruct to use markdown headings
  - [x] 3.2.3 For ADO: Instruct that fields are separate (not headings)
  - [x] 3.2.4 Write unit tests for provider-aware prompt generation

## 4. Story Points, Business Value, Priority Calculations

- [x] 4.1 Extract story points, business value, priority from providers
  - [x] 4.1.1 Ensure `GitHubFieldMapper` extracts from markdown body
  - [x] 4.1.2 Ensure `AdoFieldMapper` extracts from ADO fields
  - [x] 4.1.3 Handle missing or invalid values gracefully
  - [x] 4.1.4 Write unit tests for field extraction

- [x] 4.2 Calculate complexity score for refinement
  - [x] 4.2.1 Create complexity scoring function using story points and business value
  - [x] 4.2.2 Include complexity score in refinement validation
  - [x] 4.2.3 Use complexity score to adjust refinement confidence
  - [x] 4.2.4 Write unit tests for complexity scoring

- [x] 4.3 Implement story splitting detection
  - [x] 4.3.1 Detect stories > 13 points (Scrum threshold, configurable)
  - [x] 4.3.2 Detect multi-sprint stories (stories spanning multiple iterations, Scrum/SAFe)
  - [x] 4.3.3 Validate SAFe hierarchy (Feature → Story → Task, detect Stories without Feature parent)
  - [x] 4.3.4 Generate splitting suggestions with rationale (framework-aware)
  - [x] 4.3.5 Add story splitting suggestions to refinement output
  - [x] 4.3.6 Write unit tests for story splitting detection (Scrum, SAFe scenarios)

- [x] 4.4 Include in refinement prompts and validation
  - [x] 4.4.1 Add story points, business value, priority to refinement prompts
  - [x] 4.4.2 Validate these fields in refinement validation
  - [x] 4.4.3 Include in refinement scoring calculation
  - [x] 4.4.4 Write unit tests for refinement with story points

## 5. Custom Template-Based Field Mapping

- [x] 5.1 Create default ADO field mapping templates
  - [x] 5.1.1 Create `resources/templates/backlog/field_mappings/ado_default.yaml` (generic mappings)
  - [x] 5.1.2 Create `resources/templates/backlog/field_mappings/ado_scrum.yaml` (Scrum-specific: Product Backlog Item, Story Points, Sprint tracking)
  - [x] 5.1.3 Create `resources/templates/backlog/field_mappings/ado_agile.yaml` (Agile-specific: User Story, Story Points)
  - [x] 5.1.4 Create `resources/templates/backlog/field_mappings/ado_safe.yaml` (SAFe-specific: Epic, Feature, User Story, Value Points, WSJF)
  - [x] 5.1.5 Create `resources/templates/backlog/field_mappings/ado_kanban.yaml` (Kanban-specific: work item types, state transitions, no sprint requirement)
  - [x] 5.1.6 Document field mapping template format with framework examples

- [x] 5.2 Support custom field mappings
  - [x] 5.2.1 Load custom mappings from `.specfact/templates/backlog/field_mappings/ado_custom.yaml`
  - [x] 5.2.2 Validate custom mapping schema
  - [x] 5.2.3 Merge custom mappings with defaults (custom overrides defaults)
  - [x] 5.2.4 Write unit tests for custom mapping loading

- [x] 5.3 Add CLI support for custom mappings
  - [x] 5.3.1 Add `--custom-field-mapping` option to `specfact backlog refine` command
  - [x] 5.3.2 Allow specifying custom mapping file path
  - [x] 5.3.3 Validate custom mapping file before use
  - [x] 5.3.4 Write integration tests for CLI with custom mappings

## 6. Integration and Testing

- [x] 6.1 Update adapters to use field mappers
  - [x] 6.1.1 Update `AdoAdapter` to use `AdoFieldMapper` for extraction and writeback
  - [x] 6.1.2 Update `GitHubAdapter` to use `GitHubFieldMapper` for extraction
  - [x] 6.1.3 Ensure writeback preserves field structure (GitHub: markdown, ADO: separate fields)
  - [x] 6.1.4 Write integration tests for adapter field mapping

- [x] 6.2 Update backlog commands
  - [x] 6.2.1 Add story splitting suggestions to `specfact backlog refine` output
  - [x] 6.2.2 Display story points, business value, priority in refinement output
  - [x] 6.2.3 Add `--custom-field-mapping` option documentation
  - [x] 6.2.4 Write integration tests for backlog commands

- [x] 6.3 Comprehensive testing
  - [x] 6.3.1 Run full test suite: `hatch run smart-test-full`
  - [x] 6.3.2 Ensure ≥80% test coverage
  - [x] 6.3.3 Run contract tests: `hatch run contract-test`
  - [x] 6.3.4 Fix any linting errors: `hatch run format`
  - [x] 6.3.5 Run type checking: `hatch run type-check`

- [x] 6.4 Documentation updates
  - [x] 6.4.1 Update backlog refinement guide with field mapping information
  - [x] 6.4.2 Add custom field mapping guide
  - [x] 6.4.3 Document story splitting detection feature
  - [x] 6.4.4 Update API documentation for new `BacklogItem` fields
