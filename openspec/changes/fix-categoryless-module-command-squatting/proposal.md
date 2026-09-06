# Change: Block category-less module command squatting

## Why

Workspace modules are discovered from repository-controlled `.specfact/modules` directories. When category grouping is enabled, a category-less module can currently register an arbitrary command at the CLI root. That allows a hostile checkout to claim a removed flat command such as `validate` and execute package Python when stale automation invokes it.

## What Changes

- Skip category-less module packages during command registration when category grouping is enabled.
- Preserve the explicit legacy flat-registration behavior when category grouping is disabled.
- Add regression coverage proving a category-less workspace module cannot claim a root command or have its loader invoked in grouped mode.
- Keep categorized module registration and canonical grouped command mounting unchanged.

## Capabilities

### Modified Capabilities

- `command-package-runtime-validation`

## Impact

- **Code:** `src/specfact_cli/registry/module_packages.py` module command registration.
- **Tests:** focused registry tests for category-less packages in grouped and legacy modes.
- **Documentation:** review `README.md`, `docs/`, `docs/index.md`, and navigation; no update is expected because category-less root commands are already outside the documented grouped CLI contract.
- **Compatibility:** default grouped mode becomes fail-closed; explicitly disabled grouping retains legacy flat registration.
- **Offline behavior:** unchanged; the decision uses local manifest metadata only.
- **Rollback:** revert the registration guard and its regression tests if an unexpected supported category-less grouped module is identified.

## Source Tracking

- **GitHub Issue**: #718
- **Issue URL**: https://github.com/nold-ai/specfact-cli/issues/718
- **Parent Feature**: #352
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: Open; parent relationship to #352 and required labels are set, but project assignment is blocked because the available token cannot access the organization project.
