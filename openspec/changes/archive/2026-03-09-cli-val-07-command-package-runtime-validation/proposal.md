## Why

SpecFact `0.40.1` shipped with module discovery behavior that can surface internal duplicate-module and protocol-compliance noise during normal command startup. We need a repeatable command-by-command validation plan that exercises the released core and marketplace bundles exactly as users do, so output regressions and unexpected runtime behavior are caught before the next release.

## What Changes

- **NEW**: Define a command-package runtime validation capability that inventories core commands, installs each official bundle from the marketplace/bundled registry path, executes every command family and leaf command in a logical order, and records expected stdout/stderr/exit-code behavior.
- **MODIFY**: Tighten canonical user-module-root behavior so module discovery does not emit duplicate or shadow warnings when `~/.specfact/modules` is the configured default source being used normally.
- **MODIFY**: Tighten debug logging behavior so module-discovery diagnostics, protocol-compliance chatter, and similar internal traces remain debug-only unless there is a real actionable warning or security failure.
- **MODIFY**: Fix backlog runtime compatibility across the built-in `backlog-core` module and the published `nold-ai/specfact-backlog` marketplace bundle so overlapping command ownership does not leak duplicate-command warnings, `backlog refine ado` accepts the core ADO adapter, and `backlog map-fields` plus `backlog add` operate end-to-end with saved custom-field metadata.

## Capabilities

### New Capabilities

- `command-package-runtime-validation`: Exhaustive validation matrix for core commands and official bundle commands, including installation, execution order, output capture, and findings reporting.

### Modified Capabilities

- `user-module-root`: Canonical user-scope module discovery must stay quiet during normal startup and silently deduplicate expected default-path observations.
- `debug-logging`: Internal module-discovery diagnostics must not appear in normal command output when `--debug` is not enabled.
- `command-package-runtime-validation`: Backlog command validation must cover the live split between core and marketplace backlog packages and detect runtime incompatibilities, hidden post-selection stalls, and metadata hand-off failures.
- `backlog-runtime-compatibility`: Built-in backlog-core flows and marketplace backlog commands must interoperate without interface mismatches or lost provider-field metadata.

## Impact

- **Affected specs**: New `command-package-runtime-validation`; modified `user-module-root`; modified `debug-logging`
- **Affected specs**: New `command-package-runtime-validation`; modified `user-module-root`; modified `debug-logging`; new `backlog-runtime-compatibility`
- **Affected code**: `src/specfact_cli/registry/module_packages.py`, `src/specfact_cli/registry/module_discovery.py`, `modules/backlog-core/src/backlog_core/commands/add.py`, validation/audit tests, and the published backlog bundle code in `specfact-cli-modules`
- **Integration points**: core command registry, bundled/module marketplace installation flow, canonical `~/.specfact/modules` startup path, `specfact-cli-modules` package manifests and Typer apps, core backlog adapter interfaces, persisted backlog provider metadata, and the `backlog add` create path
- **Documentation impact**: contributor/release validation docs must describe the full command audit workflow and expected clean-output rules for non-debug runs
