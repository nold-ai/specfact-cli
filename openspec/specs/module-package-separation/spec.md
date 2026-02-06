# module-package-separation Specification

## Purpose
TBD - created by archiving change arch-02-module-package-separation. Update Purpose after archive.
## Requirements
### Requirement: Module-local command implementation

The system SHALL store each CLI command implementation inside its owning module package at `src/specfact_cli/modules/<module>/src/commands.py`.

#### Scenario: Move command implementation into module package

**Given** an existing command implementation in `src/specfact_cli/commands/<command_file>.py`

**When** that module is migrated in this change

**Then** the command implementation is moved to `src/specfact_cli/modules/<module>/src/commands.py`

**And** the module package includes `src/__init__.py`

**And** the module `src/app.py` imports `app` from the module-local `commands` module

### Requirement: Backward-compatible command shims

The system SHALL preserve backward compatibility for legacy imports from `src/specfact_cli/commands/` during migration.

#### Scenario: Legacy import path remains valid

**Given** existing code or tests import `app` from `specfact_cli.commands.<command>`

**When** a module has been migrated to module-local command implementation

**Then** `src/specfact_cli/commands/<command_file>.py` remains present as a re-export shim

**And** the shim imports `app` from `specfact_cli.modules.<module>.src.commands`

**And** command invocation behavior remains unchanged

### Requirement: Phased migration with verification gates

The system SHALL execute migration in phased waves and require verification for each wave before proceeding.

#### Scenario: Tier-based migration progression

**Given** migration tiers ordered from simplest modules to heavyweight modules

**When** a tier migration is executed

**Then** tests derived from this change spec are run for the migrated modules

**And** CLI help paths for migrated commands remain available

**And** contract-first validation passes before the next tier starts

### Requirement: Module dependency declaration integrity

The system SHALL keep `module_dependencies` accurate in each module package manifest when migration introduces module-to-module imports.

#### Scenario: Dependency declaration after migration

**Given** a migrated module imports code from another module package

**When** `module-package.yaml` is reviewed for that module

**Then** the imported module is declared under `module_dependencies`

**And** if no cross-module imports exist, `module_dependencies` remains empty

