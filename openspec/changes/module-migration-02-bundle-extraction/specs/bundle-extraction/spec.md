# bundle-extraction Specification

## Purpose

Defines the behaviour for extracting module source code from `src/specfact_cli/modules/` in the core package into independently versioned bundle package directories in `specfact-cli-modules/packages/`. Covers namespace layout, re-export shim requirements, shared-code factoring rules, and integrity re-signing after source moves.

## ADDED Requirements

### Requirement: Each bundle has a canonical package directory in specfact-cli-modules

Five bundle package directories SHALL be created in `specfact-cli-modules/packages/`, one per workflow-domain category defined by `module-migration-01`.

#### Scenario: Bundle package directory structure matches canonical layout

- **GIVEN** the canonical category-to-bundle mapping from module-migration-01 (category metadata in `module-package.yaml`)
- **WHEN** the bundle extraction is complete
- **THEN** `specfact-cli-modules/packages/` SHALL contain exactly five subdirectories: `specfact-project/`, `specfact-backlog/`, `specfact-codebase/`, `specfact-spec/`, `specfact-govern/`
- **AND** each subdirectory SHALL contain: `module-package.yaml` (top-level bundle manifest), `src/<bundle_namespace>/` (Python namespace root), `src/<bundle_namespace>/__init__.py`
- **AND** each bundle namespace SHALL follow the pattern `specfact_<category_slug>` (e.g., `specfact_codebase`, `specfact_project`)

#### Scenario: Bundle package contains all member module sources

- **GIVEN** a bundle package directory (e.g., `specfact-codebase/`)
- **WHEN** the extraction is complete
- **THEN** `src/specfact_codebase/` SHALL contain one subdirectory per member module (e.g., `analyze/`, `drift/`, `validate/`, `repro/`)
- **AND** each member subdirectory SHALL mirror the original `src/<module_name>/` structure from `src/specfact_cli/modules/<module_name>/src/<module_name>/`
- **AND** module-internal imports SHALL be updated from `specfact_cli.modules.<name>` to `specfact_<bundle_slug>.<name>`

#### Scenario: specfact-project bundle contains correct member modules

- **GIVEN** the `specfact-project` bundle
- **WHEN** the bundle package directory is inspected
- **THEN** `src/specfact_project/` SHALL contain: `project/`, `plan/`, `import_cmd/`, `sync/`, `migrate/`
- **AND** inter-member imports (e.g., `sync` importing from `plan`) SHALL remain valid within the bundle namespace

#### Scenario: specfact-backlog bundle contains correct member modules

- **GIVEN** the `specfact-backlog` bundle
- **WHEN** the bundle package directory is inspected
- **THEN** `src/specfact_backlog/` SHALL contain: `backlog/`, `policy_engine/`

#### Scenario: specfact-codebase bundle contains correct member modules

- **GIVEN** the `specfact-codebase` bundle
- **WHEN** the bundle package directory is inspected
- **THEN** `src/specfact_codebase/` SHALL contain: `analyze/`, `drift/`, `validate/`, `repro/`

#### Scenario: specfact-spec bundle contains correct member modules

- **GIVEN** the `specfact-spec` bundle
- **WHEN** the bundle package directory is inspected
- **THEN** `src/specfact_spec/` SHALL contain: `contract/`, `spec/`, `sdd/`, `generate/`

#### Scenario: specfact-govern bundle contains correct member modules

- **GIVEN** the `specfact-govern` bundle
- **WHEN** the bundle package directory is inspected
- **THEN** `src/specfact_govern/` SHALL contain: `enforce/`, `patch_mode/`

### Requirement: Re-export shims preserve specfact_cli.modules.* import paths

The `specfact_cli.modules.*` import namespace SHALL remain importable after extraction for one major version cycle.

#### Scenario: Legacy import path still resolves after extraction

- **GIVEN** code that imports `from specfact_cli.modules.validate import something`
- **WHEN** the bundle extraction is complete and re-export shims are in place
- **THEN** the import SHALL succeed without ImportError
- **AND** SHALL resolve to the actual implementation in `specfact_codebase.validate`
- **AND** a `DeprecationWarning` SHALL be emitted indicating the new canonical import path

#### Scenario: Re-export shim is a pure delegation module

- **GIVEN** a re-export shim at `src/specfact_cli/modules/<name>/src/<name>/`
- **WHEN** any attribute is accessed on the shim module
- **THEN** the shim SHALL import and re-export that attribute from the corresponding bundle namespace module
- **AND** SHALL NOT duplicate any implementation logic

#### Scenario: Shim is flagged as deprecated in type stubs

- **GIVEN** the re-export shim modules
- **WHEN** static type analysis runs (basedpyright strict)
- **THEN** shim modules SHALL be annotated with `@deprecated` or equivalent so type checkers flag usages

### Requirement: Shared code used by multiple modules is factored into specfact_cli.common

No cross-bundle private imports are permitted. Any logic used by modules in different bundles SHALL reside in `specfact_cli.common`.

#### Scenario: Pre-extraction shared-code audit identifies candidates

- **GIVEN** the module source tree before extraction
- **WHEN** a shared-code audit is run (import graph analysis)
- **THEN** any module that imports from another module in a different bundle SHALL be identified
- **AND** the imported logic SHALL be moved to `specfact_cli.common` before extraction proceeds

#### Scenario: Post-extraction import graph has no cross-bundle private imports

- **GIVEN** the five extracted bundle packages
- **WHEN** all imports are resolved
- **THEN** no module in `specfact_<bundle_a>` SHALL import from `specfact_<bundle_b>` directly (where bundle_a ≠ bundle_b)
- **AND** inter-bundle shared logic SHALL only be accessed via `specfact_cli.common`
- **AND** bundle-level dependencies (`specfact-spec` → `specfact-project`, `specfact-govern` → `specfact-project`) are handled at install time by the marketplace dependency resolver, not by direct source imports

#### Scenario: sync-plan intra-bundle dependency remains valid

- **GIVEN** the `plan` and `sync` modules both in `specfact-project`
- **WHEN** `sync` imports from `plan` within `specfact_project`
- **THEN** the import is an intra-bundle import and SHALL be permitted
- **AND** SHALL NOT be flagged by the cross-bundle import gate

### Requirement: Module-package.yaml integrity fields are updated after source move

Every `module-package.yaml` in `src/specfact_cli/modules/*/` SHALL have its `integrity_sha256` and `signature_ed25519` fields regenerated after its source is moved and shims are placed.

#### Scenario: Updated manifest passes signature verification

- **GIVEN** a module whose source has been moved and whose shim is in place
- **WHEN** `hatch run ./scripts/verify-modules-signature.py --require-signature` is run
- **THEN** the verification SHALL pass for that module
- **AND** the `integrity_sha256` in the manifest SHALL match the SHA-256 of the current (shim-containing) module directory
- **AND** the `signature_ed25519` SHALL be a valid Ed25519 signature over the manifest content

#### Scenario: Verification fails for module with stale signature

- **GIVEN** a module whose source was moved but whose `module-package.yaml` was not re-signed
- **WHEN** `hatch run ./scripts/verify-modules-signature.py --require-signature` is run
- **THEN** the verification SHALL fail with an explicit error naming the affected module
- **AND** SHALL indicate whether the failure is a checksum mismatch or signature mismatch
