# format-abstraction Specification

## Purpose

This specification defines requirements for format abstraction in backlog field mapping, enabling provider-agnostic field handling while preserving provider-specific structures.

## ADDED Requirements

### Requirement: Canonical Field Names

The system SHALL define canonical field names that abstract provider-specific field structures.

#### Scenario: Canonical field name mapping

- **GIVEN** canonical field names: `description`, `acceptance_criteria`, `story_points`, `business_value`, `priority`
- **WHEN** a field mapper converts provider-specific fields
- **THEN** provider fields are mapped to canonical names
- **AND** canonical names are used internally in `BacklogItem` model

#### Scenario: Provider-specific field preservation

- **GIVEN** a `BacklogItem` is created from an ADO work item
- **WHEN** fields are extracted and mapped to canonical names
- **THEN** original ADO field names are preserved in `provider_fields` dict
- **AND** round-trip sync can restore original field structure

### Requirement: Provider-Specific Field Extraction

The system SHALL extract fields differently based on provider structure (GitHub: markdown body, ADO: separate fields).

#### Scenario: GitHub markdown extraction

- **GIVEN** a GitHub issue with body containing markdown headings
- **WHEN** `GitHubFieldMapper` extracts fields
- **THEN** fields are extracted using markdown heading patterns
- **AND** content under headings is extracted as field values

#### Scenario: ADO separate field extraction

- **GIVEN** an ADO work item with fields in `fields` dict
- **WHEN** `AdoFieldMapper` extracts fields
- **THEN** fields are extracted directly from the `fields` dict
- **AND** field names are mapped using default or custom mappings

### Requirement: Field Mapping Configuration

The system SHALL support configurable field mappings for ADO templates.

#### Scenario: Default ADO field mapping

- **GIVEN** default ADO field mappings are defined
- **WHEN** `AdoFieldMapper` extracts fields
- **THEN** default mappings are used (e.g., `System.Description` → `description`)
- **AND** mappings work for standard ADO process templates (Scrum, Agile, Kanban)

#### Scenario: Custom ADO field mapping

- **GIVEN** a custom ADO template uses different field names
- **AND** a custom mapping file specifies the field name mappings
- **WHEN** `AdoFieldMapper` extracts fields
- **THEN** custom mappings are used instead of defaults
- **AND** unmapped fields fall back to defaults if not specified in custom mapping

#### Scenario: Field mapping validation

- **GIVEN** a custom field mapping file with invalid schema
- **WHEN** the mapping file is loaded
- **THEN** validation errors are reported
- **AND** default mappings are used as fallback

### Requirement: Round-Trip Field Preservation

The system SHALL preserve provider-specific field structures during round-trip sync.

#### Scenario: GitHub round-trip preservation

- **GIVEN** a GitHub issue is imported and refined
- **WHEN** the refined item is written back to GitHub
- **THEN** fields are written back as markdown headings in the body
- **AND** original markdown structure is preserved

#### Scenario: ADO round-trip preservation

- **GIVEN** an ADO work item is imported and refined
- **WHEN** the refined item is written back to ADO
- **THEN** fields are written back to separate ADO fields (not markdown headings)
- **AND** original ADO field structure is preserved

### Requirement: Agile Framework Work Item Type Mapping

The system SHALL map work item types correctly across providers and frameworks.

#### Scenario: Scrum work item type mapping

- **GIVEN** an ADO work item with `System.WorkItemType = "Product Backlog Item"`
- **WHEN** the item is converted to `BacklogItem`
- **THEN** the `work_item_type` field is set to "Product Backlog Item" (Scrum)
- **AND** the type is preserved for round-trip sync

#### Scenario: SAFe work item type mapping

- **GIVEN** an ADO work item with `System.WorkItemType = "Feature"` (SAFe)
- **WHEN** the item is converted to `BacklogItem`
- **THEN** the `work_item_type` field is set to "Feature" (SAFe)
- **AND** parent Epic relationship is preserved
- **AND** child User Stories are linked via parent relationships

#### Scenario: Kanban work item type mapping

- **GIVEN** a GitHub issue or ADO work item using Kanban workflow
- **WHEN** the item is converted to `BacklogItem`
- **THEN** the `work_item_type` field is set appropriately (User Story, Task, Bug, etc.)
- **AND** no sprint/iteration information is required (Kanban doesn't use sprints)
