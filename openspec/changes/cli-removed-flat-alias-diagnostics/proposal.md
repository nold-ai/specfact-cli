## Why

Primary tester validation on 2026-06-09 found that removed flat root command aliases still participate in root command error handling. In a monorepo with both user-scope and project-scope marketplace modules installed, commands such as `specfact validate --help` and `specfact plan --help` report module install or shadowing diagnostics instead of behaving as removed/unknown command paths.

Flat root aliases were already deprecated and removed from the registered command surface. The remaining diagnostic compatibility path creates a false module-version signal and sends users toward module install/shadowing investigation even when the active project module copy is installed, enabled, and usable through the canonical grouped command.

## What Changes

- Remove deprecated flat command names from root "known bundle or shim" diagnostics.
- Keep missing-module diagnostics limited to canonical installed command groups such as `code`, `project`, `spec`, `govern`, `backlog`, and other still-supported root groups.
- Ensure removed flat aliases such as `validate`, `plan`, `analyze`, `drift`, `repro`, `sync`, and `migrate` cannot produce module install, disabled, skipped, or shadowed diagnostics.
- Add regression coverage using a workspace with both user-scope and project-scope module copies so removed aliases do not reintroduce misleading shadowed-module output.
- Preserve Python import compatibility shims only where explicitly still supported; this change is about CLI root command behavior, not import-path compatibility.

## Capabilities

### Modified Capabilities

- `cli-error-guidance`
- `command-package-runtime-validation`
- `core-cli-reference`

## Impact

- Affected code: root CLI command resolution/error rendering, missing bundle command diagnostics, tests around module-not-found guidance.
- Affected docs: command references or generated guidance that mention removed flat root aliases.
- Affected tests: CLI error-contract tests, module command registration tests, monorepo/project-vs-user module availability regressions.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **Parent User Story**: [#594](https://github.com/nold-ai/specfact-cli/issues/594)
- **Parent Feature**: [#353](https://github.com/nold-ai/specfact-cli/issues/353)
- **Triggered By**: follow-up validation of `danieldekay/zettelkasten-mcp` monorepo with `uv`, user-scope modules, and project-scope modules on 2026-06-09.
- **Related Changes**: `tester-cli-reliability`, `marketplace-07-module-install-state-consistency`, `module-migration-04-remove-flat-shims`
- **Change User Story**: [#605](https://github.com/nold-ai/specfact-cli/issues/605)
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: GitHub issue created with labels `enhancement`, `openspec`, `change-proposal`, and `module-system`; native issue type/parent fields still need project-board sync if required.
- **Sanitized**: false
