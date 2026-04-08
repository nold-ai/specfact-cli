## MODIFIED Requirements

### Requirement: Backlog Feature Commands Must Be Module-Owned

The system SHALL treat `nold-ai/specfact-backlog` as the sole owner of user-facing backlog and policy command surfaces, including the active proposal backlog and GitHub planning artifacts that track future backlog and ceremony feature work.

#### Scenario: Core does not directly own backlog feature commands
- **WHEN** command registration is resolved in `specfact-cli`
- **THEN** user-facing backlog feature commands are provided by the installed backlog module
- **AND** core does not ship a parallel built-in backlog command surface for the same feature commands.

#### Scenario: Core keeps only shared backlog framework contracts
- **WHEN** backlog ownership is resolved after migration
- **THEN** core retains only shared provider integrations, generic data models, and minimal backlog contracts reused outside the backlog bundle
- **AND** backlog-only command implementations, prompt resources, templates, and refinement helpers are not owned by core.

#### Scenario: Active backlog proposals are not tracked as core-owned implementation work
- **WHEN** a pending OpenSpec change or linked GitHub issue describes backlog, scrum, kanban, safe, ceremony, or policy command behavior that belongs to `specfact-backlog`
- **THEN** that work is assigned to the modules repo planning hierarchy rather than remaining a core-repo implementation story
- **AND** the core repo retains only the shared contracts or bridge points, if any, that support the owning bundle.
