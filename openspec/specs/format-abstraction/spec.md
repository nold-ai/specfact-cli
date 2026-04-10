# format-abstraction Specification

## Purpose

TBD - created by archiving change add-generic-backlog-abstraction. Update Purpose after archive.

## Requirements

### Requirement: Format Abstraction

The system SHALL provide a `BacklogFormat` abstraction that handles serialization and deserialization of backlog items across different formats (Markdown, YAML, JSON).

#### Scenario: Markdown serialization

- **WHEN** a `BacklogItem` is serialized using `MarkdownFormat`
- **THEN** the system returns the item's `body_markdown` content, optionally with YAML frontmatter for metadata

#### Scenario: Markdown deserialization

- **WHEN** markdown content (with optional YAML frontmatter) is deserialized
- **THEN** the system creates a `BacklogItem` with body_markdown and extracts provider_fields from frontmatter

#### Scenario: YAML serialization

- **WHEN** a `BacklogItem` is serialized using `StructuredFormat` with format_type "yaml"
- **THEN** the system converts all item fields to YAML format, preserving provider_fields in metadata section

#### Scenario: YAML deserialization

- **WHEN** YAML content is deserialized
- **THEN** the system creates a `BacklogItem` with all fields populated from YAML structure

#### Scenario: JSON serialization

- **WHEN** a `BacklogItem` is serialized using `StructuredFormat` with format_type "json"
- **THEN** the system converts all item fields to JSON format, preserving provider_fields in metadata section

#### Scenario: JSON deserialization

- **WHEN** JSON content is deserialized
- **THEN** the system creates a `BacklogItem` with all fields populated from JSON structure

### Requirement: Format Detection

The system SHALL automatically detect the format of raw backlog content using heuristics.

#### Scenario: Detect JSON format

- **WHEN** raw content starts with "{" or "["
- **THEN** the system detects format as "json"

#### Scenario: Detect YAML format

- **WHEN** raw content starts with "---" or contains ":" in first line
- **THEN** the system detects format as "yaml"

#### Scenario: Default to Markdown

- **WHEN** raw content doesn't match JSON or YAML patterns
- **THEN** the system defaults to "markdown" format

### Requirement: Round-Trip Preservation

The system SHALL guarantee that serialization followed by deserialization preserves all content.

#### Scenario: Markdown round-trip

- **WHEN** a `BacklogItem` is serialized to markdown and then deserialized
- **THEN** the resulting item's `body_markdown` matches the original

#### Scenario: YAML round-trip

- **WHEN** a `BacklogItem` is serialized to YAML and then deserialized
- **THEN** all fields of the resulting item match the original, including provider_fields

#### Scenario: JSON round-trip

- **WHEN** a `BacklogItem` is serialized to JSON and then deserialized
- **THEN** all fields of the resulting item match the original, including provider_fields

### Requirement: Provider-Specific Rendering

The system SHALL render backlog item bodies into provider-specific formats when updating remote items.

#### Scenario: GitHub preserves Markdown

- **GIVEN** a BacklogItem with Markdown body
- **WHEN** the GitHub adapter updates the issue body
- **THEN** the Markdown is sent as-is.

#### Scenario: ADO renders Markdown safely

- **GIVEN** a BacklogItem with Markdown body
- **WHEN** the ADO adapter updates the work item description
- **THEN** the adapter sets the field format to Markdown where supported
- **AND** uses `/multilineFieldsFormat/System.Description` with value `Markdown`
- **AND** converts Markdown to HTML when Markdown format is not accepted.

#### Scenario: Round-trip format metadata

- **GIVEN** a provider-specific render step is applied
- **WHEN** the update succeeds
- **THEN** the adapter records the original Markdown and render format in `provider_fields`
- **AND** round-trip sync preserves the original Markdown source.

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
