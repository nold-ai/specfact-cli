## ADDED Requirements

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
