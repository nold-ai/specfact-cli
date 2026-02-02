# Change: Patch mode for backlog/spec edits (previewable, confirmable) — Δ2

## Why

Reporting findings is not enough; teams love tools that propose fixes they can safely apply. A patch pipeline that generates unified diffs for backlog body updates, OpenSpec proposal/spec updates, and config updates—with `--apply` (local) and `--write` (upstream) gating and idempotency for posted comments/updates—ensures zero accidental writes and trust by design.

## What Changes

- **NEW**: Add a patch pipeline that can generate unified diffs for: backlog issue body updates (AC improvements, missing fields), OpenSpec proposal/spec updates, config updates (policy config, mapping templates).
- **NEW**: Add `--apply` + `--write` gating: default = generate patch only; `--apply` = apply locally; `--write` = push to GitHub/ADO only with explicit confirmation.
- **NEW**: Add idempotency for posted comments/updates (no duplicates).
- **NEW**: CLI: `specfact backlog refine --patch` emits a patch file and summary; `specfact patch apply <patchfile>` applies locally with preflight check; `specfact patch apply --write` updates upstream only with explicit confirmation.
- **EXTEND**: Documentation (agile-scrum-workflows, devops-adapter-integration) for patch mode.

## Capabilities

- **patch-mode**: Patch pipeline (generate diffs for backlog body, OpenSpec, config); `--apply` (local) and `--write` (upstream) gating; idempotent posts; `backlog refine --patch`, `patch apply <file>`, `patch apply --write` with confirmation.

## Impact

- **Affected specs**: New `openspec/changes/patch-mode-preview-apply/specs/patch-mode/spec.md` (Given/When/Then for patch generation, apply local, write upstream).
- **Affected code**: New module or commands for patch pipeline (e.g. `src/specfact_cli/commands/patch_commands.py` or under backlog); `specfact patch apply`; integration with backlog refine, Policy Engine (suggest → patch).
- **Affected documentation** (<https://docs.specfact.io>): docs/guides/agile-scrum-workflows.md, docs/guides/devops-adapter-integration.md.
- **Integration points**: unify-policies-engine (suggest → patch), daily-standup-exceptions-first (standup notes patch), story-complexity-splitting-hints-support (split proposal patch).
- **Backward compatibility**: Additive; no writes without explicit `--apply` or `--write` + confirmation.

## Source Tracking

- **GitHub Issue**: #177
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/177>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
