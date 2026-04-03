## ADDED Requirements

### Requirement: Registry index supports versioned bundle dependencies

The marketplace registry `index.json` SHALL support optional version specifiers on
`bundle_dependencies` entries. Each entry MAY be either a plain module ID string (unversioned,
backward-compatible) or an object with `id` and `version` fields (versioned). The CLI installer
SHALL handle both forms.

#### Scenario: Registry entry declares a versioned bundle dependency

- **GIVEN** a registry entry with:
  ```json
  "bundle_dependencies": [
    {"id": "nold-ai/specfact-project", "version": ">=0.41.0"}
  ]
  ```
- **WHEN** the installer processes this entry
- **THEN** the installer SHALL treat `nold-ai/specfact-project` as a required dependency with
  the constraint `>=0.41.0`

#### Scenario: Registry entry declares an unversioned bundle dependency (backward compat)

- **GIVEN** a registry entry with `"bundle_dependencies": ["nold-ai/specfact-project"]`
- **WHEN** the installer processes this entry
- **THEN** the installer SHALL treat the dependency as requiring any installed version
- **AND** SHALL NOT reject existing manifests that use plain string form

### Requirement: Install-time dependency version resolution

During `specfact module install`, the system SHALL resolve all `bundle_dependencies` from both
the registry index and the module's `module-package.yaml` manifest. For each dependency:
- If the dependency is not installed, the CLI SHALL prompt the user to install it
- If the dependency is installed but its version does not satisfy the declared specifier, the CLI
  SHALL prompt the user to upgrade it
- With `--yes`, missing or mismatched dependencies SHALL be auto-resolved without prompting
- With `--skip-deps`, dependency resolution SHALL be skipped entirely (existing behaviour)

#### Scenario: Installing a module whose dependency is not installed

- **GIVEN** module A declares `bundle_dependencies: [{"id": "nold-ai/specfact-project", "version": ">=0.41.0"}]`
- **AND** `specfact-project` is NOT installed
- **WHEN** user runs `specfact module install A`
- **THEN** the CLI SHALL print:
  `A requires nold-ai/specfact-project >=0.41.0 which is not installed.`
- **AND** in interactive mode SHALL prompt: `Install nold-ai/specfact-project now? [Y/n]`
- **AND** if the user confirms, SHALL install the dependency before installing A
- **AND** if the user declines, SHALL abort with exit code 1

#### Scenario: Installing a module whose dependency version is insufficient

- **GIVEN** module A requires `nold-ai/specfact-project >=0.41.0`
- **AND** `specfact-project` is installed at version `0.40.2`
- **WHEN** user runs `specfact module install A`
- **THEN** the CLI SHALL print:
  `A requires nold-ai/specfact-project >=0.41.0 but 0.40.2 is installed.`
- **AND** in interactive mode SHALL prompt: `Upgrade nold-ai/specfact-project to satisfy constraint? [Y/n]`
- **AND** if confirmed, SHALL upgrade the dependency before installing A
- **AND** if declined, SHALL abort with exit code 1

#### Scenario: Dependency already satisfied — no prompt

- **GIVEN** module A requires `nold-ai/specfact-project >=0.41.0`
- **AND** `specfact-project` is installed at version `0.41.2`
- **WHEN** user runs `specfact module install A`
- **THEN** the CLI SHALL NOT prompt about the dependency
- **AND** SHALL log at INFO level: "Dependency nold-ai/specfact-project 0.41.2 satisfies >=0.41.0"

#### Scenario: Non-interactive / CI mode with unsatisfied dependency

- **GIVEN** the CLI is running in CI/CD mode and a dependency is not installed
- **WHEN** user runs `specfact module install A` without `--yes`
- **THEN** the CLI SHALL print the dependency error and exit non-zero
- **AND** SHALL NOT silently install the dependency
- **AND** SHALL suggest re-running with `--yes` to auto-resolve

#### Scenario: Auto-resolve dependencies with --yes

- **GIVEN** module A has an unmet dependency
- **WHEN** user runs `specfact module install A --yes`
- **THEN** the CLI SHALL install or upgrade all required dependencies automatically
- **AND** SHALL print a summary of what was auto-installed/upgraded before installing A

### Requirement: Upgrade-time dependency re-evaluation

During `specfact module upgrade`, the system SHALL re-evaluate the new version's
`bundle_dependencies` after fetching its updated manifest. If the new version introduces new
or tighter dependency requirements that are not currently satisfied, the CLI SHALL prompt the
user to resolve them before completing the upgrade.

#### Scenario: Upgraded module requires a newer version of a dependency

- **GIVEN** module A is being upgraded from `0.41.0` to `0.42.0`
- **AND** `0.42.0`'s manifest declares `nold-ai/specfact-project >=0.42.0`
- **AND** `specfact-project` is installed at `0.41.2`
- **WHEN** user runs `specfact module upgrade A`
- **THEN** the CLI SHALL print:
  `A 0.42.0 requires nold-ai/specfact-project >=0.42.0 but 0.41.2 is installed.`
- **AND** SHALL prompt: `Upgrade nold-ai/specfact-project to satisfy constraint? [Y/n]`
- **AND** if confirmed, SHALL upgrade the dependency before completing the upgrade of A
- **AND** if declined, SHALL abort the upgrade of A and leave the existing version in place

#### Scenario: Upgraded module introduces a new dependency not yet installed

- **GIVEN** module A `0.42.0` introduces a new `bundle_dependencies` entry not present in `0.41.0`
- **AND** the new dependency is not installed
- **WHEN** user runs `specfact module upgrade A`
- **THEN** the CLI SHALL prompt to install the new dependency (same flow as install-time)

#### Scenario: Upgrade with --yes auto-resolves dependency changes

- **GIVEN** an upgrade introduces new or tighter dependency requirements
- **WHEN** user runs `specfact module upgrade A --yes`
- **THEN** all dependency installs and upgrades SHALL proceed automatically without prompting

### Requirement: Core CLI compatibility check produces a clear actionable error

When a module's `core_compatibility` specifier is not satisfied by the installed CLI version,
the error message SHALL tell the user both the required range and the current CLI version, and
SHALL suggest the corrective action.

#### Scenario: Module requires a newer CLI version

- **GIVEN** module A declares `core_compatibility: ">=0.45.0,<1.0.0"`
- **AND** the installed CLI is version `0.44.0`
- **WHEN** user runs `specfact module install A`
- **THEN** the CLI SHALL print:
  `A requires SpecFact CLI >=0.45.0 but you have 0.44.0.`
  `Run: specfact upgrade  or  uvx specfact-cli@latest`
- **AND** SHALL exit non-zero without installing

#### Scenario: Module is incompatible with current CLI major version

- **GIVEN** module A declares `core_compatibility: ">=0.40.0,<1.0.0"`
- **AND** the installed CLI is version `1.0.0`
- **WHEN** user runs `specfact module install A`
- **THEN** the CLI SHALL print a clear incompatibility message with the constraint and current version
- **AND** SHALL suggest checking for a newer version of the module from the marketplace

### Requirement: Circular dependency detection

The installer SHALL detect circular `bundle_dependencies` references and abort with a clear error.

#### Scenario: Circular bundle dependency detected

- **GIVEN** module A depends on B and B depends on A
- **WHEN** the installer processes the dependency graph
- **THEN** the installer SHALL detect the cycle and print:
  `Circular dependency detected: A -> B -> A`
- **AND** SHALL abort the install with exit code 1 without installing any module in the cycle

### Requirement: Dry-run shows dependency resolution plan

The install and upgrade commands SHALL support a `--dry-run` flag that shows the full dependency
resolution plan without performing any installs or upgrades.

#### Scenario: Dry-run install shows what would be installed

- **WHEN** user runs `specfact module install A --dry-run`
- **THEN** the CLI SHALL print a dependency plan:
  ```
  Would install:
    nold-ai/specfact-project 0.41.2  (required by A >=0.41.0)
    nold-ai/A 0.42.0
  ```
- **AND** SHALL exit 0 without modifying any installed modules
