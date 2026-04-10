# CHANGE VALIDATION: backlog-core-06-refine-custom-field-writeback

## Date

2026-02-25

## Scope Reviewed

- Proposal, design, tasks, and spec delta for custom field writeback reliability and tmp import ID contract.
- Impacted runtime surfaces:
  - `src/specfact_cli/backlog/mappers/ado_mapper.py`
  - `src/specfact_cli/adapters/ado.py`
  - `src/specfact_cli/modules/backlog/src/commands.py`
  - `resources/prompts/specfact.backlog-refine.md`

## Breaking-Change Analysis

- External CLI flags: no additions/removals.
- Behavior changes:
  - ADO writeback target field selection becomes deterministic and honors custom mapping precedence.
  - Tmp import now fails explicitly when IDs are missing or mismatched instead of silently producing zero updates.
- Compatibility: low risk and backward-compatible for valid refine artifacts. Invalid artifacts now fail faster with guidance.

## Dependency Analysis

- Adapter dependency: confined to existing `AdoFieldMapper` and `AdoAdapter.update_backlog_item` interaction.
- Command dependency: confined to `backlog refine --import-from-tmp` flow and prompt/export guidance.
- No new package/runtime dependencies introduced.

## Validation Commands

```bash
openspec validate backlog-core-06-refine-custom-field-writeback --strict
```

Result: `Change 'backlog-core-06-refine-custom-field-writeback' is valid`.

## Conclusion

Change is safe to implement with focused tests covering:

1. custom mapping precedence for canonical write targets,
2. adapter patch paths for mapped fields,
3. tmp import ID mismatch failure behavior.

## Validation Addendum (2026-02-26)

### Delta Scope

- Added ADO comment endpoint API-version compatibility coverage:
  - comment activities (`/workitems/{id}/comments`) use `7.1-preview.4`
  - standard work-item and WIQL operations remain on stable `7.1`

### Validation Commands

```bash
openspec validate backlog-core-06-refine-custom-field-writeback --strict
```

Result: `Change 'backlog-core-06-refine-custom-field-writeback' is valid`.
