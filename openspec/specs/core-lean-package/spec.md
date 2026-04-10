# core-lean-package Specification

## Purpose

TBD - created by archiving change module-migration-03-core-slimming. Update Purpose after archive.

## Requirements

### Requirement: The installed specfact-cli wheel contains only the 3 core module directories in this change

After this change, the `specfact-cli` wheel SHALL include module source only for: `init`, `module_registry`, `upgrade`. The auth module directory and the remaining 17 extracted module directories (project, plan, import_cmd, sync, migrate, backlog, policy_engine, analyze, drift, validate, repro, contract, spec, sdd, generate, enforce, patch_mode) SHALL NOT be present in the installed package.

#### Scenario: Fresh install wheel contains only 3 core modules

- **GIVEN** a clean Python environment with no previous specfact-cli installation
- **WHEN** `pip install specfact-cli` completes
- **THEN** `src/specfact_cli/modules/` in the installed package SHALL contain exactly 3 subdirectories: `init/`, `module_registry/`, `upgrade/`
- **AND** neither `auth/` nor any of the 17 extracted module directories SHALL be present (project, plan, import_cmd, sync, migrate, backlog, policy_engine, analyze, drift, validate, repro, contract, spec, sdd, generate, enforce, patch_mode)

#### Scenario: pyproject.toml package includes reflect 3 core modules only

- **GIVEN** the updated `pyproject.toml`
- **WHEN** `[tool.hatch.build.targets.wheel] packages` is inspected
- **THEN** only the 3 core module source paths SHALL be listed (`init`, `module_registry`, `upgrade`)
- **AND** no path matching `src/specfact_cli/modules/{auth,project,plan,import_cmd,sync,migrate,backlog,policy_engine,analyze,drift,validate,repro,contract,spec,sdd,generate,enforce,patch_mode}` SHALL appear

#### Scenario: setup.py is in sync with pyproject.toml

- **GIVEN** the updated `setup.py`
- **WHEN** `find_packages()` and data file configuration is inspected
- **THEN** `setup.py` SHALL NOT discover or include the 17 deleted module directories
- **AND** the version in `setup.py` SHALL match `pyproject.toml` and `src/specfact_cli/__init__.py`

### Requirement: `specfact --help` on a fresh install shows ≤ 5 top-level commands

On a fresh install where no bundles have been installed, the top-level help output SHALL show at most 5 commands.

#### Scenario: Fresh install help output is lean

- **GIVEN** a fresh specfact-cli install with no bundles installed via the marketplace
- **WHEN** the user runs `specfact --help`
- **THEN** the output SHALL list at most 5 top-level commands
- **AND** SHALL include: `init`, `module`, `upgrade`
- **AND** SHALL NOT include top-level `auth`
- **AND** SHALL NOT include any of the 17 extracted module commands (project, plan, backlog, code, spec, govern, etc.) as top-level entries
- **AND** the help text SHALL include a hint directing the user to run `specfact init` to install workflow bundles

#### Scenario: Help output grows only when bundles are installed

- **GIVEN** a specfact-cli install where `specfact-backlog` and `specfact-codebase` bundles have been installed
- **WHEN** the user runs `specfact --help`
- **THEN** the output SHALL include `backlog` and `code` category group commands in addition to the 3 core commands
- **AND** SHALL NOT include category group commands for bundles that are not installed (e.g., `project`, `spec`, `govern`)

### Requirement: bootstrap.py registers only the 3 core modules unconditionally

The `src/specfact_cli/registry/bootstrap.py` module SHALL no longer contain unconditional registration calls for the 17 extracted modules. Backward-compat flat command shims introduced by module-migration-01 SHALL be removed.

#### Scenario: Bootstrap registers exactly 3 core modules on startup

- **GIVEN** the updated `bootstrap.py`
- **WHEN** `bootstrap_modules()` is called during CLI startup
- **THEN** it SHALL register module apps for exactly: `init`, `module_registry`, `upgrade`
- **AND** SHALL NOT call `register_module()` or equivalent for any of the 17 extracted modules
- **AND** SHALL NOT register backward-compat flat command shims for extracted modules

#### Scenario: Flat shim commands are absent from the CLI after shim removal

- **GIVEN** a fresh specfact-cli install with no bundles installed
- **WHEN** the user runs any former flat shim command (e.g., `specfact plan --help`, `specfact validate --help`, `specfact contract --help`)
- **THEN** the CLI SHALL return an error: "Command not found. Install the required bundle with `specfact module install nold-ai/specfact-<bundle>`."
- **AND** SHALL suggest the correct category group command and bundle install command

#### Scenario: Flat shim commands resolve after bundle install

- **GIVEN** a specfact-cli install where `specfact-project` bundle has been installed
- **WHEN** the user runs `specfact project plan --help`
- **THEN** the CLI SHALL resolve the command through the installed bundle's category group
- **AND** SHALL NOT require a flat shim

### Requirement: Category group commands mount only when the corresponding bundle is installed

The `src/specfact_cli/cli.py` and registry SHALL mount category group Typer apps only when the corresponding bundle is present and active in the module registry.

#### Scenario: Category group absent when bundle not installed

- **GIVEN** `specfact-backlog` bundle is NOT installed
- **WHEN** `specfact backlog --help` is run
- **THEN** the CLI SHALL NOT expose a `backlog` category group command
- **AND** SHALL return an error message indicating the bundle is not installed and how to install it

#### Scenario: Category group present and functional after bundle install

- **GIVEN** `specfact-codebase` bundle has been installed via `specfact module install nold-ai/specfact-codebase`
- **WHEN** `specfact code --help` is run
- **THEN** the CLI SHALL expose the `code` category group with all member sub-commands: `analyze`, `drift`, `validate`, `repro`
- **AND** all sub-commands SHALL function identically to the pre-slimming behaviour

#### Scenario: All 21 commands reachable post-migration when all bundles installed

- **GIVEN** all five category bundles are installed (project, backlog, codebase, spec, govern)
- **WHEN** any of the 21 original module commands is invoked via its category group path
- **THEN** the command SHALL execute successfully
- **AND** no command SHALL be permanently lost — only the routing has changed from flat to category-scoped
