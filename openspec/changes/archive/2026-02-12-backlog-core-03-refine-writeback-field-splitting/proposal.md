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

---

## Source Tracking

### Repository: nold-ai/specfact-cli

- **GitHub Issue**: #225
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/225>
- **Last Synced Status**: proposed
- **Sanitized**: false

---

### Repository: nold-ai/specfact-cli

- **GitHub Issue**: #227
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/227>
- **Last Synced Status**: proposed
- **Sanitized**: false
