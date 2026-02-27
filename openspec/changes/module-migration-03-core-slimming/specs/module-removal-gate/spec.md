# module-removal-gate Specification

## Purpose

Defines the pre-deletion verification gate that ensures every module directory targeted for removal from `src/specfact_cli/modules/` has a confirmed-published, signed, and installable counterpart in the marketplace registry before any source deletion is committed. The gate is implemented as a script (`scripts/verify-bundle-published.py`) and is run in the pre-flight checklist of this change and any future module removal operation.

This spec prevents the failure mode where a module is deleted from core before its marketplace bundle is available to users, leaving a gap where `specfact module install nold-ai/<bundle>` would fail even after `specfact init` requires bundle installation.

## ADDED Requirements

### Requirement: A verification gate script confirms bundle availability before any module deletion

A script SHALL exist at `scripts/verify-bundle-published.py` that, given a list of module names, checks that the corresponding bundle is published in the marketplace registry, carries a valid Ed25519 signature, and is installable (the download URL resolves and the tarball passes integrity verification).

#### Scenario: Gate script passes when all targeted modules have published bundles

- **GIVEN** the gate script is invoked with the list of 17 module names to be deleted
- **AND** all five category bundles (`specfact-project`, `specfact-backlog`, `specfact-codebase`, `specfact-spec`, `specfact-govern`) are present in `specfact-cli-modules/registry/index.json`
- **AND** each bundle entry has a valid `checksum_sha256`, `signature_url`, `download_url`, and `tier: official`
- **AND** each bundle's Ed25519 signature verifies against the tarball
- **WHEN** `python scripts/verify-bundle-published.py --modules project,plan,import_cmd,sync,migrate,backlog,policy_engine,analyze,drift,validate,repro,contract,spec,sdd,generate,enforce,patch_mode` is run
- **THEN** the script SHALL exit 0
- **AND** SHALL print a summary table: one row per module → bundle ID, version, signature status (PASS)

#### Scenario: Gate script fails when a module has no published bundle

- **GIVEN** the gate script is invoked with module names including one that has no registry entry
- **AND** `specfact-cli-modules/registry/index.json` does not contain an entry for the corresponding bundle
- **WHEN** `python scripts/verify-bundle-published.py --modules project,plan,validate` is run
- **THEN** the script SHALL exit with a non-zero exit code (1)
- **AND** SHALL print a clear error message naming the module(s) with no published bundle
- **AND** SHALL NOT allow the deletion to proceed (the gate is fail-closed)

#### Scenario: Gate script fails when bundle signature verification fails

- **GIVEN** a bundle entry exists in `index.json` but the Ed25519 signature does not verify against the tarball
- **WHEN** the gate script checks that bundle
- **THEN** the script SHALL exit 1
- **AND** SHALL report: "Bundle specfact-<name>: SIGNATURE INVALID — do not delete module source until bundle is re-signed and re-published"

#### Scenario: Gate script fails when bundle download URL is unreachable (offline)

- **GIVEN** the gate script is run in an offline environment
- **WHEN** the script attempts to resolve the download URL
- **THEN** the script SHALL report: "Bundle specfact-<name>: download URL unreachable — verify offline or set SPECFACT_BUNDLE_CACHE_DIR"
- **AND** SHALL exit 1 unless `--skip-download-check` flag is passed
- **AND** SHALL still verify the cached tarball's checksum and signature if `SPECFACT_BUNDLE_CACHE_DIR` is set and the tarball is present

### Requirement: The gate script maps each module name to its correct bundle

The gate script SHALL use the `category` and `bundle` fields from each `module-package.yaml` to determine which bundle must be published for a given module name.

#### Scenario: Module-to-bundle mapping is derived from module-package.yaml

- **GIVEN** the gate script is invoked
- **WHEN** it processes a module name (e.g., `validate`)
- **THEN** it SHALL read `src/specfact_cli/modules/validate/module-package.yaml`
- **AND** SHALL extract the `bundle` field (e.g., `specfact-codebase`)
- **AND** SHALL look up `specfact-codebase` in the registry index

#### Scenario: All 17 non-core modules map to exactly one of the five bundles

- **GIVEN** the module-to-bundle mapping from all 17 non-core `module-package.yaml` files
- **WHEN** the mapping is inspected
- **THEN** every module SHALL map to one of: `specfact-project`, `specfact-backlog`, `specfact-codebase`, `specfact-spec`, `specfact-govern`
- **AND** no module SHALL be unmapped (gate fails if `bundle` field is absent from `module-package.yaml`)

### Requirement: The gate script is run as part of the pre-flight checklist for module removal

The gate script is a mandatory pre-flight check. The module source deletion MUST NOT be committed to git until the gate script exits 0.

#### Scenario: Pre-deletion checklist run completes successfully before commit

- **GIVEN** the developer is ready to commit the deletion of 17 module directories
- **WHEN** they run the pre-deletion checklist:
  1. `python scripts/verify-bundle-published.py --modules project,plan,import_cmd,sync,migrate,backlog,policy_engine,analyze,drift,validate,repro,contract,spec,sdd,generate,enforce,patch_mode`
  2. `hatch run ./scripts/verify-modules-signature.py --require-signature` (for remaining 4 core modules)
- **THEN** both commands SHALL exit 0 before any `git add` of deleted files is permitted
- **AND** the developer SHALL include the gate script output in `openspec/changes/module-migration-03-core-slimming/TDD_EVIDENCE.md` as pre-deletion evidence

#### Scenario: Gate script is idempotent and safe to re-run

- **GIVEN** the gate script has already been run successfully
- **WHEN** it is run again with the same arguments
- **THEN** it SHALL produce the same output and exit 0 (assuming no registry changes)
- **AND** SHALL NOT modify any files, registries, or module manifests

### Requirement: The gate enforces the NEVER-remove-before-published invariant as a contract

The gate script SHALL use `@require` and `@beartype` contracts to enforce that module names are non-empty, the registry file exists, and the index is parseable JSON before any verification logic runs.

#### Scenario: Gate script contracts reject empty module list

- **GIVEN** the gate script is invoked with an empty module list (`--modules ""`)
- **WHEN** the precondition contract is evaluated
- **THEN** the script SHALL fail with a contract violation error before any I/O is performed
- **AND** SHALL print: "Precondition violated: at least one module name must be specified"

#### Scenario: Gate script contracts reject missing registry index

- **GIVEN** `specfact-cli-modules/registry/index.json` does not exist
- **WHEN** the gate script is invoked
- **THEN** the script SHALL fail with: "Registry index not found at <path> — ensure module-migration-02 is complete before running module removal"
- **AND** SHALL exit 1

### Requirement: Future module removals reuse the same gate script

The gate is not specific to this change. It SHALL be reusable for any future removal of bundled module source from the core package.

#### Scenario: Gate is invoked for a single module removal

- **GIVEN** a hypothetical future change that removes only `src/specfact_cli/modules/migrate/`
- **WHEN** `python scripts/verify-bundle-published.py --modules migrate` is run
- **THEN** the script SHALL check that `specfact-project` (the bundle containing `migrate`) is published and verified
- **AND** SHALL exit 0 if the check passes, 1 if it fails
