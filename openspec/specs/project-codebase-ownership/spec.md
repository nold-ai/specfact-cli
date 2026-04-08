# project-codebase-ownership Specification

## Purpose
TBD - created by archiving change module-migration-11-project-codebase-ownership-realignment. Update Purpose after archive.
## Requirements
### Requirement: Codebase Commands Own Code-First Brownfield Workflows

The system SHALL treat commands whose primary input is a source codebase or runtime code evidence as `code` category commands.

#### Scenario: Brownfield import is code-owned
- **WHEN** the user runs the canonical code-first brownfield import workflow
- **THEN** the workflow resolves from the `specfact code ...` command surface
- **AND** `specfact code import` is treated as the canonical codebase-owned entrypoint rather than a project-owned path in the target command model.

#### Scenario: Compatibility alias is transitional only
- **GIVEN** a temporary compatibility alias exists for a pre-realignment path such as `specfact project import from-code`
- **WHEN** the command is invoked during the migration window
- **THEN** the system routes to the code-owned implementation
- **AND** the alias is documented as compatibility behavior rather than the canonical ownership model.

### Requirement: Project Commands Own SpecFact Bundle Artifact Lifecycle

The system SHALL reserve the `project` category for commands whose primary subject is the SpecFact project bundle/workspace and its editable artifacts.

#### Scenario: Project surface manages bundle artifacts
- **WHEN** a command primarily selects, reviews, edits, imports, exports, migrates, or otherwise manages SpecFact project bundle artifacts
- **THEN** that command belongs to the `specfact project ...` surface
- **AND** the command is not classified as codebase-owned solely because the artifact may later be synchronized with source code.

### Requirement: Brownfield Analysis Internals Have A Single Canonical Owner

Subsystems that implement code-first brownfield analysis SHALL have one documented canonical bundle owner.

#### Scenario: Analysis subsystems align with codebase ownership
- **WHEN** bundle ownership is resolved for brownfield analysis internals
- **THEN** `analyzers`, `comparators`, brownfield-oriented `parsers`, and related import-analysis helpers are assigned to the codebase owner unless an explicit documented exception exists
- **AND** migration plans, runtime registration, and docs do not describe contradictory owners for the same subsystem family.

### Requirement: Pending Changes Must Align With The Ownership Decision

Pending OpenSpec changes that touch command surface, docs, prompts, migration cleanup, or issue planning SHALL align with the canonical post-migration ownership model instead of reintroducing monolithic `specfact-cli` module ownership by implication.

#### Scenario: Active change does not finalize conflicting import ownership
- **GIVEN** an active pending change updates grouped command paths or release-facing docs
- **WHEN** that change references brownfield import ownership
- **THEN** it references the canonical owner defined by this change
- **AND** it does not re-establish a conflicting public command path or subsystem owner by implication.

#### Scenario: Active proposal does not preserve obsolete in-repo module paths
- **GIVEN** an active proposal still describes implementation under `modules/<name>/` in `specfact-cli` for a capability now owned by a bundle in `specfact-cli-modules`
- **WHEN** maintainers reconcile the proposal against the current architecture
- **THEN** the proposal is updated to the correct repository and bundle ownership model
- **AND** any remaining core-repo scope is reduced to the shared runtime, contract, or integration surface that core still owns.

