## ADDED Requirements

### Requirement: Architecture Review Finding Model

The system SHALL define an architecture review finding model covering boundary, interface, ADR, and Well-Architected review concerns.

#### Scenario: Architecture findings use canonical categories

- **WHEN** an architecture review finding is emitted
- **THEN** its category is one of `boundary-violation`, `interface-leak`, `layer-inversion`, `coupling-hotspot`, `missing-adr`, `wa-operational-excellence`, `wa-security`, `wa-reliability`, `wa-performance`, `wa-cost`, or `wa-sustainability`
- **AND** the rule id is deterministic for that category and check.

#### Scenario: Architecture findings integrate with shared review reporting

- **GIVEN** a review run emits architecture findings
- **WHEN** the shared report envelope is serialized
- **THEN** it contains an `architecture` section
- **AND** other review sections are preserved unchanged.

### Requirement: Interface Diff Command

The system SHALL provide `specfact architecture diff --since <ref>` that classifies interface changes as breaking, additive, or non-breaking.

#### Scenario: Breaking interface change is classified explicitly

- **GIVEN** a public interface removes a required parameter or narrows its return contract
- **WHEN** the diff command compares the current tree against a prior reference
- **THEN** the change is classified as `breaking`
- **AND** the output identifies the affected interface surface.

#### Scenario: Additive change remains non-breaking

- **GIVEN** a public interface adds an optional parameter with a default
- **WHEN** the diff command evaluates the change
- **THEN** the change is classified as `additive`
- **AND** the result remains consumable by review and governance tooling.

### Requirement: Maintained Python dependency evidence

After architecture inputs ship and one complete real usage cycle, the first Python dependency-rule slice SHALL consume maintained Import Linter results. It SHALL retain exact source/configuration/tool/rule identity and associate violations with declared boundaries without building a duplicate import-graph engine. Unavailable, incomplete or wrong-snapshot extraction SHALL remain UNKNOWN. Findings SHALL retain original report references and the actual supported core compatibility range.

#### Scenario: Forbidden dependency planted

- **GIVEN** a supported Python fixture violating a declared dependency boundary
- **WHEN** Import Linter evidence is consumed
- **THEN** the planted violation is associated with its boundary, source and original rule.

#### Scenario: Extraction unavailable

- **GIVEN** the required analyzer cannot produce complete current-snapshot results
- **WHEN** the boundary is evaluated
- **THEN** it is UNKNOWN and no empty graph is treated as proof of conformance.
