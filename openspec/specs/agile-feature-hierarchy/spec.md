# agile-feature-hierarchy Specification

## Purpose
Keep the public SpecFact CLI backlog organized as a three-level GitHub hierarchy of Epic -> Feature -> User Story, with `openspec/CHANGE_ORDER.md` kept in sync with the current planning structure.
## Requirements
### Requirement: GitHub Agile Feature Hierarchy
The project governance workflow SHALL maintain a three-level GitHub planning hierarchy of Epic -> Feature -> User Story for the public SpecFact CLI backlog.

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
