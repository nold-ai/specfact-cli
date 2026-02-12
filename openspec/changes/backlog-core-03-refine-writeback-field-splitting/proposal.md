# Change: Backlog Refine Writeback Field Splitting for ADO/GitHub

## Why

`specfact backlog refine --write` currently applies the raw copilot response as `body_markdown` and does not parse structured refinement output back into canonical fields before adapter writeback. For Azure DevOps this causes `System.Description` to receive a verbatim payload containing labels like `Description`, `Acceptance Criteria`, `Story Points`, `Business Value`, `Priority`, `Area Path`, and provider markers instead of updating separate fields. GitHub can exhibit the same issue when copilot output uses label-style sections instead of markdown headings.

This breaks the provider-aware contract implied by refinement prompts and produces low-quality remote item updates.

## What Changes

- **MODIFY**: Backlog refine write path to parse structured refinement content into canonical fields (`description`, `acceptance_criteria`, `story_points`, `business_value`, `priority`, `work_item_type`) before writeback.
- **MODIFY**: Normalize label-style refinement output to canonical markdown sections so both ADO and GitHub writeback paths behave deterministically.
- **MODIFY**: ADO/GitHub writeback behavior to prefer parsed refined values over stale pre-refinement values when `--write` is used.
- **MODIFY**: Refactor `backlog refine` orchestration in `commands.py` into smaller helper methods (initialization, export/import handling, writeback/comment flow) to reduce command-function complexity and improve readability.
- **ADD**: Regression tests for ADO and GitHub writeback from label-style refinement output.

## Capabilities

- **backlog-refinement**: Provider-aware parsing and canonical field splitting for `specfact backlog refine --write`.

## Impact

- **Affected specs**: `openspec/specs/backlog-refinement/spec.md`
- **Affected code**:
  - `src/specfact_cli/modules/backlog/src/commands.py`
  - `src/specfact_cli/adapters/ado.py`
  - `src/specfact_cli/adapters/github.py`
  - `tests/unit/backlog/` and/or `tests/integration/backlog/`
- **Integration points**:
  - `BacklogAIRefiner` prompt output contract
  - `BacklogItem` refinement application path
  - Adapter writeback mapping for ADO and GitHub
- **Documentation impact**:
  - Update user-facing backlog refine docs if command behavior wording currently implies guaranteed field splitting without this parsing path.

## Rollback Plan

- Revert parser integration in refine write path and adapter fallback logic.
- Keep tests to preserve observed failure mode for future rework.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: TBD
- **Issue URL**: TBD
- **Last Synced Status**: proposed
- **Sanitized**: false
