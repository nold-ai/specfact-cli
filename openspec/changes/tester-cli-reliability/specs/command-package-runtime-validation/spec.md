## MODIFIED Requirements

### Requirement: Command Inventory Covers Core And Official Bundles

The system SHALL derive a validation inventory that covers the released core commands and every official command package shipped from `specfact-cli-modules`.

#### Scenario: Inventory includes core commands and official bundle roots

- **GIVEN** the core module manifests under `src/specfact_cli/modules/`
- **AND** the official bundle manifests under `specfact-cli-modules/packages/`
- **WHEN** the runtime validation inventory is generated
- **THEN** it includes `specfact`, `init`, `module`, and `upgrade`
- **AND** it includes the official bundle roots `project`, `spec`, `code`, `backlog`, and `govern`
- **AND** every inventory entry records the owning package and command path.

#### Scenario: Inventory expands nested subcommands from Typer apps

- **GIVEN** a bundle root command with nested Typer groups or leaf commands
- **WHEN** the runtime validation inventory is generated
- **THEN** nested command paths are expanded from the Typer application tree
- **AND** the inventory includes grouped paths such as `backlog ceremony standup`, `project sync bridge`, `spec contract validate`, `code validate sidecar run`, and `govern patch apply`
- **AND** a missing nested command path fails validation instead of being silently skipped.

#### Scenario: Inventory feeds AI-agent command overview artifacts

- **GIVEN** the runtime validation inventory is generated
- **WHEN** command overview artifacts are written
- **THEN** the same inventory data is used for `llms.txt`, Markdown, JSON, docs validation, and runtime smoke selection
- **AND** validators do not use a separate manually maintained command allowlist for canonical commands.

### Requirement: Validation Matrix Executes Commands In Logical Runtime Order

The system SHALL execute the command inventory in a deterministic order that matches normal user setup and runtime dependencies.

#### Scenario: Core setup executes before bundle commands

- **GIVEN** a validation run starts in a clean workspace
- **WHEN** the command-package runtime audit runs
- **THEN** it executes root help and startup checks before any bundle commands
- **AND** it executes `specfact init`, `specfact module`, and `specfact upgrade` validation cases before bundle installation or bundle-root validation
- **AND** installation/bootstrap failures stop later phases from being reported as passed.

#### Scenario: Bundle command phases follow installation order

- **GIVEN** the official bundles are available from bundled artifacts or marketplace registry sources
- **WHEN** the audit installs and validates bundle commands
- **THEN** bundle roots are validated after install/bootstrap succeeds
- **AND** nested command families are executed under their owning root in a stable order
- **AND** the audit report shows which phase each command belonged to.

### Requirement: Package Manager Runtime Matrix Blocks Command Mismatches

The command validation surface SHALL run through representative hatch, pip, pipx, and uv launchers before PRs can merge.

#### Scenario: Runtime matrix exercises installed CLI paths

- **GIVEN** a pull request changes CLI runtime, module discovery, command docs, or packaging behavior
- **WHEN** CI runs the package-manager runtime matrix
- **THEN** it builds and executes the CLI through hatch source execution, pip wheel install, pipx install, uv run, and uv tool or uvx execution paths
- **AND** it validates representative core and official module command groups in each path
- **AND** any command path, module discovery, or install-method mismatch blocks the PR.

#### Scenario: Pipx upgrade validates and repairs stale launcher

- **GIVEN** `specfact upgrade` is running from a pipx-managed installation
- **AND** `pipx upgrade specfact-cli` exits successfully
- **WHEN** the installed `specfact --version` launcher fails because it still points at a stale or missing pipx venv path
- **THEN** the upgrader runs `pipx reinstall specfact-cli`
- **AND** it validates `specfact --version` again after the reinstall
- **AND** it reports failure if the launcher still cannot execute.
