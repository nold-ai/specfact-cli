# Change: backlog-core-07 - ADO Required Custom Fields and Picklist Validation

## Why

`specfact backlog add --adapter ado` can fail when required custom fields exist and field constraints include allowed picklist values. Today, users can supply values that are not valid for the selected work item type, and the command does not consistently guide them to resolvable values in interactive or non-interactive mode.

## What Changes

- Extend `specfact backlog map-fields` to dynamically detect required custom fields per ADO work item type and persist requirement metadata for add-time validation.
- Extend `specfact backlog add --adapter ado` interactive flow to fetch eligible picklist values from ADO and let users choose with an up/down picker.
- Extend non-interactive add flow to validate provided values against allowed values and return actionable error hints listing accepted choices.
- Ensure required mapped custom fields are enforced in payload assembly before ADO create calls.
- Add contract-first and unit/integration tests for required-field discovery, interactive chooser behavior, and non-interactive value validation errors.
- Update user-facing docs for `backlog map-fields` and `backlog add` custom field/picklist behavior.

## Capabilities

### New Capabilities

- `ado-field-value-selection`: Interactive selection workflow for ADO constrained field values during backlog add.

### Modified Capabilities

- `backlog-map-fields`: Requirement discovery for ADO custom fields includes dynamic required flags and eligible value metadata by work item type.
- `backlog-add`: ADO add flow enforces required custom fields and validates constrained values in interactive and non-interactive modes.

## Impact

- **Affected code**:
  - `src/specfact_cli/modules/backlog/src/backlog/commands/map_fields.py`
  - `src/specfact_cli/modules/backlog/src/backlog/commands/add.py`
  - `src/specfact_cli/modules/backlog/src/backlog/services/*` (field metadata/payload validation paths)
  - `src/specfact_cli/adapters/ado/` (field metadata and allowed-values retrieval)
  - Tests under `tests/unit/` and `tests/integration/` for backlog map/add and ADO adapter behavior
- **Affected specs**: `backlog-map-fields`, `backlog-add`, new `ado-field-value-selection`
- **Backward compatibility**: Non-interactive mode becomes stricter for invalid constrained values, with explicit allowed-values hints. Valid existing flows remain compatible.
- **Dependencies**: ADO field metadata endpoints must be reachable for interactive constrained selection; offline/non-interactive fallback remains deterministic with validation against persisted metadata when available.
- **Rollback plan**: Revert map/add validation enhancements and fall back to previous payload handling behavior.
- **Documentation updates required**:
  - `docs/` command reference for `backlog map-fields` and `backlog add`
  - `README.md` backlog add guidance where custom fields are discussed
  - `docs/index.md` only if command discovery text changes

## Source Tracking

- **GitHub Issue**: #337
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/337>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: synced by reporter (2026-03-04)
- **Sanitized**: false
