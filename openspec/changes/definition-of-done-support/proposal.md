# Change: Definition of Done (DoD) support

## Why

SpecFact CLI has Definition of Ready (DoR) for backlog refinement (readiness for sprint planning). Teams also need Definition of Done (DoD) to ensure items moved to "Done" meet completion criteria. DoD is not modeled or validated today; there is no way to define team DoD rules (e.g. checklist: tests pass, docs updated, code reviewed) and run them against items in Done state.

## What Changes

- **NEW**: Model DoD as a checklist or rule set (similar in spirit to DoR but for completion). Store DoD config per project (e.g. `.specfact/dod.yaml` or under templates).
- **NEW**: When listing or exporting backlog items in "Done" (or equivalent) state, optionally run DoD validation and attach DoD status (pass/fail + which criteria failed).
- **EXTEND**: Integrate into the **backlog command group** (e.g. `specfact backlog list`, `specfact backlog refine`, or a dedicated `specfact backlog dod` / `specfact backlog validate` subcommand): for items in done state, show DoD status in output and export. Do not add a top-level scrum/DoD command.
- **EXTEND**: Documentation (agile-scrum-workflows, backlog-refinement) for DoD workflow.

## Capabilities

- **definition-of-done**: DoD config load, DoD validation for done items, DoD status in CLI/export when enabled.

## Impact

- **Affected specs**: New `openspec/changes/definition-of-done-support/specs/definition-of-done/spec.md` (Given/When/Then for DoD config, validation, status output).
- **Affected code**: `src/specfact_cli/` (DoD config and validator); `src/specfact_cli/commands/backlog_commands.py` (optional DoD check for done items under backlog group).
- **Affected documentation** (<https://docs.specfact.io>): docs/guides/agile-scrum-workflows.md, docs/guides/backlog-refinement.md for DoD.
- **Integration points**: Existing backlog list/refine/export; BacklogItem state=Done; DoR patterns for reuse.
- **Backward compatibility**: Additive only; existing backlog behavior unchanged unless user opts into DoD validation.

## Source Tracking

- **GitHub Issue**: #169
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/169>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
