# Change: Fix custom field mapping reliability in backlog refine writeback

## Why

`specfact backlog refine --import-from-tmp --write` can write ADO story points to a default field (`Microsoft.VSTS.Common.StoryPoints`) even when custom mapping or framework mapping requires another field (for example `Microsoft.VSTS.Scheduling.StoryPoints` or custom process fields). This causes persistent writeback failures and incorrect field updates in Copilot-mode refinement workflows.

Additionally, `specfact backlog daily --post` and related comment-write paths can fail in some Azure DevOps tenants when comment activity calls use stable `7.1` instead of the comments preview API version required by those endpoints.

## What Changes

- **MODIFY** ADO writeback field target resolution so canonical fields (`story_points`, `acceptance_criteria`, `business_value`, `priority`) consistently resolve to the effective mapped provider field with deterministic precedence.
- **MODIFY** backlog refine tmp export/import guidance to require preserving per-item `**ID**` for successful lookup and writeback.
- **MODIFY** tmp import behavior to fail fast with an actionable error when parsed refined blocks do not match any fetched backlog item IDs.
- **MODIFY** backlog prompt templates under `resources/prompts/specfact.backlog-*.md` to document exact parser-required tmp/input structure for each backlog command path.
- **MODIFY** ADO extraction normalization so body and acceptance criteria rich text are consistently converted to markdown-like text before refine/export/writeback operations.
- **MODIFY** ADO comment endpoint version routing so comment activities (`/workitems/{id}/comments`) use `7.1-preview.4` while standard work item and WIQL operations remain on stable `7.1`.
- **EXTEND** tests across mapper, adapter, and command import flows to prove custom mapping reliability and ID contract enforcement.

## Capabilities

### New Capabilities
- `backlog-refine-writeback-mapping`: deterministic write-target selection for mapped provider fields during backlog refine writeback.

### Modified Capabilities
- `backlog-refinement`: refine export/import contract and failure handling for mandatory item IDs.
- `format-abstraction`: normalize ADO rich text/HTML backlog fields to markdown-like text for canonical backlog model usage.
- `backlog-daily`: ADO comment posting/readback paths use endpoint-appropriate API versions.

## Impact

- Affected code:
  - `src/specfact_cli/backlog/mappers/ado_mapper.py`
  - `src/specfact_cli/adapters/ado.py`
  - `src/specfact_cli/backlog/converter.py`
  - `src/specfact_cli/modules/backlog/src/commands.py`
  - `resources/prompts/specfact.backlog-*.md`
  - tests under `tests/unit/adapters/`, `tests/unit/backlog/`, `tests/unit/commands/`
- Affected behavior:
  - ADO field writeback in refine flows now respects configured mapping priority for all mapped canonical fields.
  - Tmp import requires stable `**ID**` keys and surfaces explicit mismatch errors instead of silently producing zero updates.
  - ADO comment posting and retrieval use comments-preview API version compatibility while core work-item operations stay on stable `7.1`.
- Dependencies: no new runtime dependency; relies on existing ADO mapper and backlog adapter abstractions.
