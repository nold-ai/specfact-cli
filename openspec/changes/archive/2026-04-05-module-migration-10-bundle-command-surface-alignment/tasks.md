# Tasks

## 1. Audit And Classify The Missing Command Paths

- [x] 1.1 Build a documented grouped-command inventory for the affected `project` and `spec` surfaces from README/docs/release-content references.
- [x] 1.2 Verify each documented path against the installed official bundle runtime.
- [x] 1.3 Classify each missing path as `public-runtime`, `docs-only-drift`, or `owner-decision-required`.

## 2. Update Specs And Failing Tests First

- [x] 2.1 Add or update spec deltas for documented grouped command-path parity.
- [x] 2.2 Add failing regression tests for the currently missing public-runtime paths.
- [x] 2.3 Record pre-implementation failing evidence in `TDD_EVIDENCE.md`.

## 3. Fix Bundle Runtime Exposure

- [x] 3.1 Patch the affected official bundles in `specfact-cli-modules` so intended grouped subcommands are mounted and reachable.
- [x] 3.2 Verify the installed-bundle command tree exposes the intended grouped paths end-to-end.
- [x] 3.3 Avoid adding new core CLI shims to compensate for bundle registration gaps.

## 4. Align Release Documentation

- [x] 4.1 Update README/docs/release-facing examples in `specfact-cli` for any `docs-only-drift` paths.
- [x] 4.2 Ensure public docs do not describe missing grouped commands as available in `v0.40.x`.
- [x] 4.3 Capture any website/blog follow-up that must be synchronized outside this repo.

## 5. Validate And Record Evidence

- [x] 5.1 Re-run targeted command-surface tests for the fixed paths.
- [x] 5.2 Extend or re-run command-package runtime validation for the documented grouped paths.
- [x] 5.3 Record post-implementation passing evidence in `TDD_EVIDENCE.md`.
- [x] 5.4 Run `openspec validate module-migration-10-bundle-command-surface-alignment --strict`.
