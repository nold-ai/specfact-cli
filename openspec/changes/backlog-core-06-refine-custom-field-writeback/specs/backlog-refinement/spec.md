## MODIFIED Requirements

### Requirement: Abstract Field Mapping Layer

The system SHALL provide an abstract field mapping layer that normalizes provider-specific field structures to canonical field names.

#### Scenario: ADO writeback resolves mapped story points field deterministically

- **GIVEN** an ADO work item refine writeback with `story_points` set
- **AND** multiple candidate ADO fields map to `story_points` (for example default and custom mappings)
- **WHEN** writeback field resolution runs
- **THEN** the system selects the effective write target with deterministic precedence: explicit custom mapping first, then provider-present mapped fields, then framework/default fallback
- **AND** the PATCH operation uses the resolved mapped field (for example `Microsoft.VSTS.Scheduling.StoryPoints` or a custom field)
- **AND** the system does not silently fall back to a non-selected default field.

#### Scenario: ADO writeback resolves all mapped canonical fields consistently

- **GIVEN** canonical update values for `acceptance_criteria`, `story_points`, `business_value`, and `priority`
- **WHEN** ADO writeback builds PATCH operations
- **THEN** each canonical field uses the same mapped write-target resolution strategy
- **AND** custom mappings apply consistently across all canonical fields supported by ADO mapper configuration.

### Requirement: Backlog Item Refinement Command

The system SHALL provide a `specfact backlog refine` command that enables teams to standardize backlog items using AI-assisted template matching and refinement.

#### Scenario: Refined tmp import requires stable item IDs

- **GIVEN** a refined markdown artifact intended for `--import-from-tmp`
- **WHEN** the artifact is parsed
- **THEN** each `## Item N:` block MUST include an `**ID**` property copied from the export
- **AND** import rejects artifacts that omit required IDs for item lookup.

#### Scenario: Refined tmp import reports ID mismatch explicitly

- **GIVEN** a refined markdown artifact with parsed item blocks
- **AND** none of the parsed `**ID**` values match fetched backlog items for the current refine command filters
- **WHEN** import processing runs
- **THEN** the command exits with an explicit error describing the ID mismatch
- **AND** the message instructs the user to preserve exported IDs unchanged.

#### Scenario: `any` disables state/assignee filtering

- **GIVEN** a user runs backlog commands that support state/assignee filters (for example `daily` or `refine`)
- **WHEN** the user passes `--state any` and/or `--assignee any`
- **THEN** the system treats the respective filter as disabled (no filter applied)
- **AND** command output/help makes this behavior explicit so default scoping is understandable.

### Requirement: ADO comment activities use endpoint-compatible API versioning

The system SHALL use the preview ADO comments API version for comment read/write activities while preserving stable `7.1` for standard work-item operations.

#### Scenario: ADO daily/refine comment posting uses preview comments endpoint version

- **GIVEN** a configured ADO adapter posts a comment to `/workitems/{id}/comments`
- **WHEN** the adapter builds and executes the comment POST request
- **THEN** the request targets `api-version=7.1-preview.4`
- **AND** standard ADO work-item or WIQL operations continue using `api-version=7.1`.
