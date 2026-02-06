# Change: Module Package Separation for Command Implementations

## Why

The modular registry introduced in arch-01 created module packages, but command implementations still live in `src/specfact_cli/commands/` and module `src/app.py` files are mostly re-export shims. This keeps command ownership centralized and increases merge conflict risk when multiple modules evolve in parallel.

To complete the modular architecture, each command implementation needs to live inside its own module package while preserving backward compatibility for existing imports and command loading behavior.

## What Changes

- **NEW**: Define and execute a phased migration pattern that moves command implementations from `src/specfact_cli/commands/*.py` into `src/specfact_cli/modules/<module>/src/commands.py`.
- **NEW**: Require module-local `src/app.py` wiring (`from ...src.commands import app`) and module-local `src/__init__.py` scaffolding for each migrated module.
- **NEW**: Require backward-compatible re-export shims in `src/specfact_cli/commands/*.py` so external and legacy imports remain stable during migration, including temporary re-export of currently used non-`app` symbols.
- **NEW**: Require per-module verification (CLI help, contract-first tests, relevant module tests) and phased rollout from simplest modules to heavyweight modules.
- **NEW**: Require decoupling work that extracts cross-command helper symbols into shared core modules (`utils`, `models`, or dedicated shared modules), then migrates imports off `specfact_cli.commands.*`.
- **NEW**: Require a boundary guard in tests/CI so new cross-command imports (`specfact_cli.commands.*` non-`app`) cannot be introduced after migration waves.
- **EXTEND**: Require migration tasks to include documentation review and updates where architecture docs or contributor guidance reference the old command layout.

## Capabilities

- **module-package-separation**: Migrate command implementations into module packages with compatibility shims and phased validation.

## Impact

- **Affected specs**: New `openspec/changes/arch-02-module-package-separation/specs/module-package-separation/spec.md`.
- **Affected code**: `src/specfact_cli/commands/`, `src/specfact_cli/modules/*/src/`, and module-local test locations under `src/specfact_cli/modules/*/tests/` where applicable.
- **Affected documentation** (<https://docs.specfact.io>): Any architecture or contributor docs that describe command locations and module boundaries; likely includes `README.md`, `AGENTS.md`, and potentially docs architecture/reference pages if they mention `src/specfact_cli/commands` as implementation home.
- **Integration points**: Module discovery/registry loading via existing module package entrypoints (`src/app.py`), CLI command help and invocation behavior, contract-first test workflows.
- **Backward compatibility**: Preserved in transition by command-level re-export shims for `app` plus currently used legacy symbols; then reduced toward `app`-only once dependents are migrated.

## Source Tracking

- **GitHub Issue**: #199
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/199>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
