# ado-field-value-selection Specification

## Purpose

TBD - created by archiving change backlog-core-07-ado-required-custom-fields-and-picklists. Update Purpose after archive.

## Requirements

### Requirement: Interactive constrained value selection for ADO custom fields

The system SHALL provide an interactive picker for ADO mapped custom fields that expose constrained allowed values.

#### Scenario: Picker navigates constrained value list

- **GIVEN** constrained values are available for an ADO mapped custom field
- **WHEN** the user opens the field picker and presses up/down keys
- **THEN** the highlighted value changes accordingly
- **AND** pressing Enter confirms the current value.

#### Scenario: Picker fallback when constrained values are unavailable

- **GIVEN** constrained values are unavailable because metadata lookup fails
- **WHEN** interactive add requests that field
- **THEN** the command falls back to text input with a warning
- **AND** add-time validation still checks persisted constraints when available.
