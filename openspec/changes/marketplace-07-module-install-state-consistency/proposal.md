## Why

SpecFact module installation, discovery, init profile bootstrap, and command registration can disagree about whether a module is usable. Users can see a command group reported as not installed, then be told by `specfact module install` that the same module is already installed or already available, which makes recovery unreliable across user and project scopes.

## What Changes

- Reconcile module install no-op paths with lifecycle state so an already-present module is either enabled for the selected scope or reported as installed-but-disabled with an actionable command.
- Improve missing command diagnostics so they distinguish absent modules from disabled, shadowed, incompatible, dependency-skipped, or integrity/schema-skipped modules.
- Make init/profile state refreshes preserve unrelated module state and avoid cwd-derived surprises when `--repo` selects a repository.
- Normalize install/discovery/state identity comparisons so bare names, marketplace IDs, and manifest IDs resolve to one canonical module record before deciding that work is already satisfied.
- Add focused regression tests for repeated `module install`, `init --profile`, user/project scope shadowing, and disabled-module recovery.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `module-installation`: install no-op behavior must account for module lifecycle state and command availability, not just the presence of `module-package.yaml`.
- `user-module-root`: user/project scope discovery and shadowing must remain deterministic and must surface actionable guidance when an installed module is shadowed or scope-specific.
- `init-module-state`: init/profile bootstrap must preserve user lifecycle choices while avoiding accidental global state churn from a different cwd or repo context.

## Impact

- Affected code: `src/specfact_cli/modules/module_registry/src/commands.py`, `src/specfact_cli/registry/module_packages.py`, `src/specfact_cli/registry/module_discovery.py`, `src/specfact_cli/registry/module_state.py`, `src/specfact_cli/modules/init/src/commands.py`, and `src/specfact_cli/cli.py`.
- Affected tests: module registry command tests, lifecycle/state tests, discovery tests, init/profile tests, and CLI missing-command tests.
- User impact: module commands become recoverable and diagnostics stop sending users through contradictory install loops.
- GitHub tracking: fixes bug [#533](https://github.com/nold-ai/specfact-cli/issues/533), syncs to user story [#534](https://github.com/nold-ai/specfact-cli/issues/534), and both issues are children of Feature [#353](https://github.com/nold-ai/specfact-cli/issues/353).

## Source Tracking

- Source type: GitHub + OpenSpec
- Source repo: `nold-ai/specfact-cli`
- Bug report: [#533](https://github.com/nold-ai/specfact-cli/issues/533)
- Synced user story: [#534](https://github.com/nold-ai/specfact-cli/issues/534)
- Parent feature: [#353](https://github.com/nold-ai/specfact-cli/issues/353) `[Feature] Marketplace Module Distribution`
- Report origin: direct user workflow feedback on 2026-04-28
