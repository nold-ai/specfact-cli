## Why

Three user bug reports show clean installed-runtime discovery gaps in SpecFact CLI 0.46.18:

- `#552` and `#554`: `nold-ai/specfact-codebase` is installed and enabled, but `specfact code` can report that the module is not installed or can show only timing output instead of command help.
- `#553`: `specfact init ide` reports no compatible environment manager in rootless monorepos even when `uv` is available on `PATH` and package-level `pyproject.toml` files exist.

The failures are core runtime issues, not module ownership issues. Installed module command loading, missing-command diagnostics, and environment-manager detection live in `specfact-cli`.

## What Changes

- **EXTEND** installed module runtime loading so lazy command import makes all enabled discovered module `src/` roots importable before loading a module command app.
- **EXTEND** missing command diagnostics so an installed-but-unloadable module reports the real runtime/import cause instead of a false "not installed" message.
- **NEW** environment-manager detection behavior for rootless monorepos and PATH-only tool availability.
- **EXTEND** `specfact init ide` with `--env-manager <auto|uv|hatch|poetry|pip>` while keeping automatic detection as the default.

## Capabilities

### Modified Capabilities

- `installed-runtime-module-discovery`
- `module-installation`
- `module-owned-ide-prompts`

### New Capabilities

- `environment-manager-detection`

## Impact

- Affected code: module discovery/command loading, module availability diagnostics, environment-manager detection, and `init ide` option wiring.
- Affected tests: targeted unit/e2e tests for installed module runtime loading, missing command diagnostics, monorepo environment detection, and `init ide --env-manager`.
- GitHub scope: fixes `#552`, `#553`, and `#554`; all remain in `nold-ai/specfact-cli` and are blocked by dedicated user-story issue `#557`, which is tracked under feature parent `#353`.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **Parent Feature**: [#353](https://github.com/nold-ai/specfact-cli/issues/353)
- **Change User Story**: [#557](https://github.com/nold-ai/specfact-cli/issues/557)
- **GitHub Issues**: [#552](https://github.com/nold-ai/specfact-cli/issues/552), [#553](https://github.com/nold-ai/specfact-cli/issues/553), [#554](https://github.com/nold-ai/specfact-cli/issues/554)
- **Issue Relationships**: `#557` blocks `#552`, `#553`, and `#554`; no direct user bug report is nested under an epic or feature.
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: GitHub story and dependencies synced
- **Sanitized**: false
