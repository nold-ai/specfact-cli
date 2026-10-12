# Change: Block category-less module command squatting

## Why

Workspace modules are discovered from repository-controlled `.specfact/modules` directories. When category grouping is
enabled, a category-less module can currently register an arbitrary command at the CLI root. That allows a hostile
checkout to claim a removed flat command such as `validate` and execute package Python when stale automation invokes
it.

## What Changes

- Skip category-less project/workspace packages during command registration when category grouping is enabled; preserve
other discovery sources.
- Preserve the explicit legacy flat-registration behavior when category grouping is disabled.
- Add regression coverage proving a category-less workspace module cannot claim a root command or have its loader
invoked in grouped mode.
- Reserve permanent core root commands for resolved built-in package paths in every mode; reject category/core and
source-label impersonation. Reject project packages that claim official category roots before any registration side
effects; keep eligible categorized module registration unchanged.

## Capabilities

### Modified Capabilities

- `module-grouping` (amend the existing registration and missing-category requirement)
- `command-package-runtime-validation` (reserve permanent and official category root commands)
- `category-command-groups` (reconcile the shipped categorized-routing behavior in disabled grouping mode)

## Impact

- **Code:** `src/specfact_cli/registry/module_packages.py` module command registration.
- **Tests:** focused registry tests for category-less packages in grouped and legacy modes.
- **Documentation:** review `README.md`, `docs/`, `docs/index.md`, and navigation; no update is expected because
category-less root commands are already outside the documented grouped CLI contract.
- **Compatibility:** default grouped mode becomes fail-closed; explicitly disabled grouping retains legacy flat
registration.
- **Offline behavior:** unchanged; the decision uses local manifest metadata only.
- **Rollback:** revert the registration guard and its regression tests if an unexpected supported category-less grouped
module is identified.

## Source Tracking

- **GitHub Issue**: #718
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/718>
- **Parent Feature**: #352
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: Open; parent relationship to #352 and required labels are set, project assignment is verified
as SpecFact CLI/Todo and native dependency lists are empty.

## Prior protected validation cycle after #761

Prerequisite #760 shipped through #761 into protected dev at c4ee5be8457f69848bf9bc2150ebc3df56b52d4f.
The protected helper authenticates unchanged inherited runtime proof while preserving #743/#751 as planning.
The prior candidate f6481418 was re-authored against that baseline with accepted mapping e550f23e and native RED
before implementation. No earlier-head proof, candidate helper or stale acceptance substitutes for the new cycle.
That cycle prepared coherent 0.55.8 artifacts after RED and left all three targets unmerged for owner review.

## Protected consumer integration after #767 (2026-10-12)

Merged #767 is protected dev c6af68a0fdf2ea798dd22c6750f077e217c938f5, version 0.55.8.
The earlier security candidate f6481418 passed all current-head gates and review on its original base.
Re-author specification and unchanged accepted controls against this new base before restoring production.
Owner acceptance e550f23e remains exact and genuine; new signed-head grants and native proof are required.
Current security bugfix release is the next available patch, 0.55.9. Leave #719/#743/#751 unmerged.
