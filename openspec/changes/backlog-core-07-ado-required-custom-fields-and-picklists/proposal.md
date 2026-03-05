# Change: backlog-core-07 - ADO Required Custom Fields and Picklist Validation

## Why


`specfact backlog add --adapter ado` can fail when required custom fields exist and field constraints include allowed picklist values. Today, users can supply values that are not valid for the selected work item type, and the command does not consistently guide them to resolvable values in interactive or non-interactive mode.

## What Changes


- Extend `specfact backlog map-fields` to dynamically detect required custom fields per ADO work item type and persist requirement metadata for add-time validation.
- Add a non-interactive `specfact backlog map-fields` mode that auto-discovers and applies deterministic mappings; fail with guidance to run interactive mapping only when auto-mapping cannot resolve required fields.
- Extend `specfact backlog add --adapter ado` to accept repeatable `--custom-field key=value` input and merge mapped custom fields into create payload.
- Extend add interactive flow to fetch eligible picklist values from ADO and let users choose with an up/down picker for constrained fields.
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

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #337
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/337>
- **Issue State**: OPEN (checked 2026-03-05)
- **Modules PRs**:
  - <https://github.com/nold-ai/specfact-cli-modules/pull/9> (merged to `dev`)
  - <https://github.com/nold-ai/specfact-cli-modules/pull/11> (merged `dev` -> `main`)
- **Modules Publish Verification Run**:
  - <https://github.com/nold-ai/specfact-cli-modules/actions/runs/22725544343> (pass)
- **Core PR**: pending (this change still requires coordinated core-side finalization before archive)
- **Last Synced Status**: modules-merged-core-pending
- **Sanitized**: false
