# Change: Backlog Core — Installed Runtime Discovery Parity and Backlog Add Prompt

## Why

`specfact backlog add` and related backlog-core commands are available in development (`hatch run specfact`) but can be missing from PyPI-installed runtime command surfaces, even at the same version. This creates a production usability regression where documented commands are unavailable after upgrade.

Additionally, `backlog add` currently lacks a dedicated slash-command prompt in `resources/prompts/`, resulting in inconsistent IDE workflow coverage compared to `backlog refine` and `backlog daily`.

## What Changes

- **MODIFY**: Module discovery root fallback logic so installed runtime can discover workspace-level `modules/` when invoked from a repo checkout, restoring parity with development command surfaces.
- **MODIFY**: Add tests for installed-runtime discovery path behavior and command-surface parity assumptions.
- **NEW**: Add `resources/prompts/specfact.backlog-add.md` slash prompt for the new `backlog add` workflow.
- **MODIFY**: Extend IDE setup command list so the new backlog-add prompt is installed automatically into IDE command folders.
- **MODIFY**: Add/update tests that verify IDE template installation includes backlog-add prompt.

## Capabilities

- **backlog-core** (extended): Installed runtime command-surface parity for workspace module discovery.
- **backlog** (extended): Backlog add slash-command prompt parity with existing backlog prompt workflows.

## Impact

- **Affected specs**:
  - `openspec/changes/backlog-core-04-installed-runtime-discovery-and-add-prompt/specs/installed-runtime-module-discovery/spec.md`
  - `openspec/changes/backlog-core-04-installed-runtime-discovery-and-add-prompt/specs/backlog-add-slash-prompt/spec.md`
- **Affected code**:
  - `src/specfact_cli/registry/module_packages.py`
  - `src/specfact_cli/utils/ide_setup.py`
  - `resources/prompts/specfact.backlog-add.md`
- **Affected tests**:
  - `tests/unit/specfact_cli/registry/test_module_packages.py`
  - `tests/unit/utils/test_ide_setup.py`
- **Documentation impact**:
  - `docs/reference/commands.md` (slash prompt mention for backlog add, if needed)

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: TBD
- **Issue URL**: TBD
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
