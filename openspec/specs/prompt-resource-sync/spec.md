# prompt-resource-sync Specification

## Purpose

TBD - created by archiving change backlog-core-05-user-modules-bootstrap. Update Purpose after archive.

## Requirements

### Requirement: Prompt Resource Detection and Project Target Copy

The system SHALL consistently detect bundled prompt resources and copy them to IDE-specific project target paths during IDE initialization.

#### Scenario: Installed runtime resolves bundled prompt resources

- **GIVEN** SpecFact is installed and invoked outside repository checkout context
- **WHEN** prompt resource resolution runs during `specfact init ide`
- **THEN** the resolver finds bundled `resources/prompts` templates from installed package locations
- **AND** prompt installation proceeds without requiring repository-local prompt files.

#### Scenario: IDE setup copies detected prompts to project target

- **GIVEN** prompt templates are detected
- **WHEN** `specfact init ide` copies templates for a selected IDE
- **THEN** prompt files are created in the expected project target folder for that IDE
- **AND** backlog-related prompts (including `specfact.backlog-add`) are included.
