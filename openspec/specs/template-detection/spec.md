# template-detection Specification

## Purpose
TBD - created by archiving change add-template-driven-backlog-refinement. Update Purpose after archive.
## Requirements
### Requirement: Template Detection Engine

The system SHALL detect which template (if any) a backlog item matches, returning confidence scores and missing fields.

#### Scenario: High-confidence template match

- **WHEN** a backlog item contains all required sections for a template and matches pattern rules
- **THEN** the system returns template_id with confidence >= 0.8 and empty missing_fields list

#### Scenario: Medium-confidence template match

- **WHEN** a backlog item contains most required sections but is missing some optional sections
- **THEN** the system returns template_id with confidence 0.5-0.8 and lists missing sections

#### Scenario: Low-confidence or no match

- **WHEN** a backlog item doesn't match any template structure or patterns
- **THEN** the system returns None for template_id with confidence < 0.5

#### Scenario: Structural fit scoring

- **WHEN** template detection analyzes a backlog item
- **THEN** the system scores structural fit (60% weight) by checking presence of required section headings

#### Scenario: Pattern fit scoring

- **WHEN** template detection analyzes a backlog item
- **THEN** the system scores pattern fit (40% weight) by matching title and body regex patterns

#### Scenario: Weighted confidence calculation

- **WHEN** both structural and pattern scores are computed
- **THEN** the system calculates final confidence as weighted average: 0.6 × structural_score + 0.4 × pattern_score

### Requirement: Template Definition Schema

The system SHALL support template definitions with required sections, optional sections, regex patterns, and OpenSpec schema references.

#### Scenario: Template with required sections

- **WHEN** a template defines required_sections: ["As a", "I want", "Acceptance Criteria"]
- **THEN** template detection checks for these exact or fuzzy-matched headings in backlog items

#### Scenario: Template with regex patterns

- **WHEN** a template defines body_patterns: {"as_a": "As a [^,]+ I want"}
- **THEN** template detection matches this pattern against item body content

#### Scenario: Template with OpenSpec schema reference

- **WHEN** a template defines schema_ref: "openspec/templates/user_story_v1/"
- **THEN** the system can validate refined items against the referenced OpenSpec schema

### Requirement: Persona and Framework Template Support

The system SHALL support persona-specific and framework-specific templates with priority-based resolution.

#### Scenario: Persona-specific template matching

- **WHEN** a template defines `personas: ["product-owner"]` and user specifies `--persona product-owner`
- **THEN** the system prioritizes this template over framework-agnostic templates

#### Scenario: Framework-specific template matching

- **WHEN** a template defines `framework: "scrum"` and user specifies `--framework scrum`
- **THEN** the system prioritizes this template over framework-agnostic templates

#### Scenario: Provider-specific template matching

- **WHEN** a template defines `provider: "ado"` and user refines items from Azure DevOps adapter
- **THEN** the system prioritizes this template over provider-agnostic templates

#### Scenario: Combined template matching

- **WHEN** a template matches provider+framework+persona (e.g., `provider: "ado"`, `framework: "scrum"`, `personas: ["product-owner"]`)
- **THEN** the system selects this template with highest priority, falling back to less specific matches if not found

#### Scenario: Template resolution fallback chain

- **WHEN** no exact match is found for provider+framework+persona
- **THEN** the system falls back through: provider+framework → framework+persona → framework → provider+persona → persona → provider → default template

### Requirement: Common Backlog Filtering

The system SHALL support filtering backlog items by common fields (labels/tags, state, assignees) and iteration/sprint identifiers.

#### Scenario: Filter by labels/tags

- **WHEN** a user specifies `--labels "feature,enhancement"`
- **THEN** the system fetches only backlog items with matching labels/tags (using BacklogItem.tags field)

#### Scenario: Filter by state

- **WHEN** a user specifies `--state "open"`
- **THEN** the system fetches only backlog items with matching state (using BacklogItem.state field)

#### Scenario: Filter by assignee

- **WHEN** a user specifies `--assignee "user1"`
- **THEN** the system fetches only backlog items assigned to the specified user (using BacklogItem.assignees field)

### Requirement: Iteration and Sprint Filtering

The system SHALL support filtering backlog items by iteration, sprint, and release identifiers.

#### Scenario: Filter by iteration path

- **WHEN** a user specifies `--iteration "Project\\Sprint 1"`
- **THEN** the system fetches only backlog items with matching iteration path

#### Scenario: Filter by sprint

- **WHEN** a user specifies `--sprint "Sprint 1"`
- **THEN** the system fetches only backlog items with matching sprint identifier

#### Scenario: Filter by release

- **WHEN** a user specifies `--release "Release 1.0"`
- **THEN** the system fetches only backlog items with matching release identifier

#### Scenario: Provider-specific iteration extraction

- **WHEN** a backlog item is created from Azure DevOps with `System.IterationPath: "Project\\Sprint 1"`
- **THEN** the system extracts sprint "Sprint 1" and iteration "Project\\Sprint 1" into normalized fields

#### Scenario: Provider-specific milestone extraction

- **WHEN** a backlog item is created from GitHub with milestone "Sprint 1"
- **THEN** the system extracts sprint "Sprint 1" into normalized field, preserving original milestone data in provider_fields

