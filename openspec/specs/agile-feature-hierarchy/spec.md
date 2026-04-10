# agile-feature-hierarchy Specification

## Purpose

Keep the public SpecFact CLI backlog organized as a three-level GitHub hierarchy of Epic -> Feature -> User Story, with `openspec/CHANGE_ORDER.md` kept in sync with the current planning structure.

## Requirements

### Requirement: GitHub Agile Feature Hierarchy

The project governance workflow SHALL maintain a three-level GitHub planning hierarchy of Epic -> Feature -> User Story for the public SpecFact CLI backlog, and SHALL expose the current Epic and Feature metadata through a repo-local hierarchy cache before manual GitHub lookups are used.

#### Scenario: Feature issues group user stories under the correct epic

- **GIVEN** the public backlog contains Epic issues and change-proposal issues
- **WHEN** the hierarchy setup work is completed
- **THEN** each planned Feature issue is linked to its parent Epic
- **AND** each grouped User Story issue is assigned to the correct Feature

#### Scenario: CHANGE_ORDER stays aligned with the GitHub hierarchy

- **GIVEN** new Epic or Feature-level hierarchy items are introduced in GitHub
- **WHEN** the change is updated
- **THEN** `openspec/CHANGE_ORDER.md` reflects the current Epic and Feature sequencing metadata
- **AND** stale issue state such as archived-but-open items is reconciled during validation

#### Scenario: Local cache is consulted before manual hierarchy lookup

- **GIVEN** a contributor needs a parent Feature or Epic while creating or syncing a change issue
- **WHEN** the local hierarchy cache is present and current
- **THEN** the contributor can resolve the parent relationship from the cache without an additional GitHub lookup
- **AND** the sync script is rerun only when the cache is stale or missing
