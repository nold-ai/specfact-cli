# Change Validation: init-ide-prompt-source-selection

- Date: 2026-03-25
- Command: `openspec validate init-ide-prompt-source-selection --strict`
- Result: `Change 'init-ide-prompt-source-selection' is valid`

## Scope Review

- The change was narrowed to `specfact-cli` orchestration only.
- Bundle-owned prompt/template payload migration remains in `specfact-cli-modules` change `packaging-01-bundle-resource-payloads` (`nold-ai/specfact-cli-modules#101`).
- Installed-resource discovery mechanics remain owned by `packaging-02-cross-platform-runtime-and-module-resources` in `specfact-cli`.

## Dependency Review

- `backlog-module-ownership-cleanup` remains a prerequisite so backlog prompt ownership is no longer split across core and bundle code.
- `specfact-cli-modules#101` is now treated as the paired payload provider for bundle-owned prompt/template resources.
- `module-migration-11-project-codebase-ownership-realignment` is treated as command-surface alignment context so exported prompts do not reassert obsolete ownership or grouped command paths.

## Behavioral Boundaries Confirmed

- `specfact init ide` is an anytime re-sync/export command.
- `specfact init ide` discovers installed resources from effective module roots; it does not download or install module archives.
- Install/bootstrap guidance continues to belong to `specfact module init` and `specfact module install` with user/project scope selection.
