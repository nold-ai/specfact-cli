## 1. Spec And Dependency Setup

- [x] 1.1 Update spec deltas so this change owns only core-side orchestration: root-aware prompt/resource source discovery, default `all` export behavior, interactive source selection, and non-interactive `--prompts` parsing.
- [x] 1.2 Confirm the final prompt ownership inputs from `backlog-module-ownership-cleanup`, `packaging-02-cross-platform-runtime-and-module-resources`, and `specfact-cli-modules/packaging-01-bundle-resource-payloads`.
- [x] 1.3 Align exported prompt ownership and recommendations with the active command-surface decisions from `module-migration-11-project-codebase-ownership-realignment`.

## 2. Test-First Prompt Source Selection

- [x] 2.1 Add failing tests for default export of all available prompt sources.
- [x] 2.2 Add failing tests for effective source discovery across built-in, user-scope, project-scope, and custom module roots.
- [x] 2.3 Add failing tests for interactive multi-select over `core` plus installed module ids.
- [x] 2.4 Add failing tests for non-interactive `--prompts` values including `all`, `core`, mixed selections, and invalid/non-installed module ids.
- [x] 2.5 Add failing tests that missing prompt/resource payloads emit install/bootstrap guidance instead of downloading modules from `init ide`.
- [x] 2.6 Record the failing evidence in `TDD_EVIDENCE.md`.

## 3. Implementation

- [x] 3.1 Extend prompt-source discovery so `specfact init ide` sees the effective installed module roots for the current repo context, including user and project scope.
- [x] 3.2 Update `specfact init ide` interactive flow to use a source picker over the discovered installed prompt sources.
- [x] 3.3 Add non-interactive `--prompts` selection using comma-separated source tokens.
- [x] 3.4 Ensure copied prompt resources are namespaced by source and collision-safe.
- [x] 3.5 Add actionable scope-aware guidance that points users to `specfact module init` / `specfact module install` when selected resources are missing.
- [x] 3.6 Keep `init ide` as an anytime re-sync command that copies discovered resources only and does not perform install/download/extract work itself.

## 4. Validation

- [x] 4.1 Re-run the new prompt-selection and root-discovery tests and record passing evidence in `TDD_EVIDENCE.md`.
- [x] 4.2 Update docs/help text for `specfact init ide`, `specfact module init`, and `specfact module install` so scope ownership and refresh behavior are explicit.
- [x] 4.3 Run `openspec validate init-ide-prompt-source-selection --strict`.
