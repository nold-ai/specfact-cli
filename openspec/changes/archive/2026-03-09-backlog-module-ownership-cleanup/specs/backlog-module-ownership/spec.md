## ADDED Requirements

### Requirement: Backlog Feature Commands Must Be Module-Owned

The system SHALL treat `nold-ai/specfact-backlog` as the sole owner of user-facing backlog and policy command surfaces.

#### Scenario: Core does not directly own backlog feature commands

- **WHEN** command registration is resolved in `specfact-cli`
- **THEN** user-facing backlog feature commands are provided by the installed backlog module
- **AND** core does not ship a parallel built-in backlog command surface for the same feature commands.

#### Scenario: Core keeps only shared backlog framework contracts

- **WHEN** backlog ownership is resolved after migration
- **THEN** core retains only shared provider integrations, generic data models, and minimal backlog contracts reused outside the backlog bundle
- **AND** backlog-only command implementations, prompt resources, templates, and refinement helpers are not owned by core.

### Requirement: Backlog Prompt And Template Assets Must Be Module-Owned

Backlog-specific prompts, prompt templates, and backlog template semantics SHALL be owned by the backlog module, not by `specfact-cli` core.

#### Scenario: Backlog refinement assets are not exported from core

- **WHEN** backlog-specific prompt/template resources are resolved
- **THEN** they come from the backlog module resource set
- **AND** core retains only generic framework/template infrastructure, if any.

### Requirement: Normal Registration Must Not Depend On Backlog Overlap Tolerance

The system SHALL not rely on duplicate backlog command overlap handling for normal runtime registration.

#### Scenario: Backlog registration is single-owned

- **WHEN** the backlog module is installed and enabled
- **THEN** normal registration does not require suppressing duplicate backlog command collisions between core and module code
- **AND** users do not see duplicate backlog-extension warnings caused by split ownership.
