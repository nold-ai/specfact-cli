## ADDED Requirements

### Requirement: Backlog Add Slash Prompt

The system SHALL provide and install a slash prompt for `backlog add` consistent with other backlog workflows.

#### Scenario: Prompt file exists for backlog add

- **GIVEN** prompt templates in `resources/prompts/`
- **WHEN** templates are validated or inspected
- **THEN** `resources/prompts/specfact.backlog-add.md` exists
- **AND** it includes frontmatter description and `$ARGUMENTS` input placeholder.

#### Scenario: IDE setup installs backlog add prompt

- **GIVEN** `specfact init ide` (or equivalent IDE setup path) copies SpecFact templates
- **WHEN** template copying runs for an IDE target
- **THEN** a `specfact.backlog-add` prompt file is created in the IDE-specific destination
- **AND** installation behavior matches existing prompt commands.
