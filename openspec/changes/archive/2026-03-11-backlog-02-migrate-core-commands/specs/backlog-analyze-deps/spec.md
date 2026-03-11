# backlog-analyze-deps Specification

## ADDED Requirements

### Requirement: Restore backlog dependency analysis

The system SHALL provide `specfact backlog analyze-deps` for dependency graph analysis.

#### Scenario: Analyze-deps shows item dependencies
- **WHEN** the user runs `specfact backlog analyze-deps --project-id <id>`
- **THEN** the backlog dependency graph is built
- **AND** parent/child and blocking relationships are displayed

#### Scenario: Cycle detection highlights issues
- **WHEN** the dependency graph contains cycles
- **THEN** cycles are detected and reported as warnings
- **AND** affected items are listed for resolution

#### Scenario: Impact surface for selected item
- **WHEN** the user analyzes deps for a specific item
- **THEN** upstream and downstream dependencies are highlighted
