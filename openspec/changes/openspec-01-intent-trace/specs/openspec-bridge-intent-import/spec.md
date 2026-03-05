## ADDED Requirements

### Requirement: Bridge Adapter Intent Import
The system SHALL extend `specfact sync bridge --adapter openspec` with an `--import-intent` flag that reads the `## Intent Trace` YAML block from imported proposals and creates corresponding `.specfact/requirements/{id}.req.yaml` artifacts.

#### Scenario: Intent import creates BusinessOutcome artifacts
- **GIVEN** an OpenSpec proposal with a `## Intent Trace` section containing at least one `business_outcomes` entry
- **WHEN** `specfact sync bridge --adapter openspec --import-intent` is run
- **THEN** a `.specfact/requirements/{id}.req.yaml` file is created for each `BusinessOutcome` in the intent trace
- **AND** each artifact validates against the `BusinessOutcome` Pydantic schema without errors

#### Scenario: Intent import creates BusinessRule artifacts
- **GIVEN** an OpenSpec proposal with `business_rules` entries in the `## Intent Trace` section
- **WHEN** `specfact sync bridge --adapter openspec --import-intent` is run
- **THEN** each `BusinessRule` (id, outcome_ref, given, when, then) is stored in the corresponding `.req.yaml` artifact under its parent `BusinessOutcome`
- **AND** the `outcome_ref` is resolved to a valid `BusinessOutcome` ID in the imported requirements

#### Scenario: Intent import skips existing artifacts without --overwrite
- **GIVEN** a `.specfact/requirements/BO-001.req.yaml` file already exists
- **WHEN** `specfact sync bridge --adapter openspec --import-intent` is run without `--overwrite`
- **THEN** the existing file is not modified
- **AND** the CLI output notes the skipped artifact with its ID

#### Scenario: Intent import overwrites with --overwrite flag
- **GIVEN** a `.specfact/requirements/BO-001.req.yaml` file already exists
- **WHEN** `specfact sync bridge --adapter openspec --import-intent --overwrite` is run
- **THEN** the existing file is updated with the content from the proposal's intent trace section
- **AND** the CLI output confirms the overwritten artifact ID

#### Scenario: Import without --import-intent ignores intent trace section
- **GIVEN** an OpenSpec proposal with a `## Intent Trace` section
- **WHEN** `specfact sync bridge --adapter openspec` is run without `--import-intent`
- **THEN** no `.specfact/requirements/` artifacts are created
- **AND** the section is validated but not imported

### Requirement: Task-Level Requirement References
The system SHALL support an optional `requirement_refs` list field on individual tasks in OpenSpec `tasks.md` files, linking tasks to specific `BusinessRule` or `ArchitecturalConstraint` IDs.

#### Scenario: Bridge adapter parses requirement_refs in tasks
- **GIVEN** a `tasks.md` file with a task containing `requirement_refs: ["BR-001", "AC-002"]`
- **WHEN** the bridge adapter imports the proposal
- **THEN** the imported task record includes the requirement ref IDs
- **AND** they are included in the project bundle's task metadata

#### Scenario: Advisory validation warns on unresolved requirement refs
- **GIVEN** a task with `requirement_refs: ["BR-999"]` where BR-999 does not exist in `.specfact/requirements/`
- **WHEN** `specfact sync bridge --adapter openspec` is run
- **THEN** the CLI emits an advisory warning: `[ADVISORY] Task X: requirement_refs contains unknown ID BR-999`
- **AND** the import proceeds without failing
