# user-module-root Specification

## Purpose
TBD - created by archiving change backlog-core-05-user-modules-bootstrap. Update Purpose after archive.
## Requirements
### Requirement: Canonical User Module Root

The system SHALL use a canonical per-user module root at `<user-home>/.specfact/modules` for installed module artifacts and discovery.

#### Scenario: Installer defaults to user module root

- **GIVEN** a module is installed via module installer workflow without explicit install root override
- **WHEN** installation runs
- **THEN** module artifacts are installed under `<user-home>/.specfact/modules/<module-id>`
- **AND** subsequent module discovery includes that module as installed.

#### Scenario: Discovery includes user root independent of CWD

- **GIVEN** modules are present under `<user-home>/.specfact/modules`
- **AND** current working directory has no local `.specfact/modules` folder
- **WHEN** module discovery runs
- **THEN** modules from `<user-home>/.specfact/modules` are discovered
- **AND** command availability does not depend on repository-local module folders.

#### Scenario: Workspace root discovery is scoped to .specfact

- **GIVEN** current working directory contains `<repo>/modules/<module-id>`
- **AND** current working directory does not contain `<repo>/.specfact/modules/<module-id>`
- **WHEN** module discovery runs
- **THEN** `<repo>/modules/<module-id>` is not auto-discovered
- **AND** discovery does not assume ownership of non-`.specfact` repository directories.

#### Scenario: Workspace-local module discovery uses .specfact/modules

- **GIVEN** current working directory contains `<repo>/.specfact/modules/<module-id>`
- **WHEN** module discovery runs
- **THEN** `<repo>/.specfact/modules/<module-id>` is discovered as a custom workspace module root.

### Requirement: Module Init User-Root Bootstrap

`specfact module init` SHALL bootstrap shipped modules into the canonical user module root so shipped command groups are available after bootstrap.

#### Scenario: Module init seeds shipped modules to user root

- **GIVEN** an installed runtime with shipped module artifacts available in packaged or workspace source paths
- **AND** `<user-home>/.specfact/modules` does not contain those modules yet
- **WHEN** `specfact module init` runs
- **THEN** shipped modules are copied/synced into `<user-home>/.specfact/modules`
- **AND** module list/enablement includes seeded modules in the same module init run.

### Requirement: Module Init Target Scope

`specfact module init` SHALL support explicit bootstrap target scope selection.

#### Scenario: Module init defaults to user scope

- **GIVEN** no explicit target-scope switch is provided
- **WHEN** `specfact module init` runs
- **THEN** shipped modules are seeded into `<user-home>/.specfact/modules`.

#### Scenario: Module init supports project scope under .specfact

- **GIVEN** the user chooses project scope
- **AND** no explicit repo path is provided
- **WHEN** `specfact module init` runs
- **THEN** shipped modules are seeded into `<cwd>/.specfact/modules`
- **AND** project-scope bootstrap does not write into `<cwd>/modules`.

#### Scenario: Module init supports explicit repo for project scope

- **GIVEN** the user chooses project scope
- **AND** an explicit repo path `<repo>` is provided
- **WHEN** `specfact module init` runs
- **THEN** shipped modules are seeded into `<repo>/.specfact/modules`
- **AND** no module artifacts are written outside `<repo>/.specfact/modules` for that operation.

### Requirement: Project Module Precedence

Workspace project modules SHALL take precedence over user-scope modules.

#### Scenario: Project module shadows user module with same id

- **GIVEN** `<repo>/.specfact/modules/<module-id>` exists
- **AND** `<user-home>/.specfact/modules/<module-id>` exists
- **WHEN** module discovery runs in `<repo>`
- **THEN** the discovered module source for `<module-id>` resolves to project scope
- **AND** command behavior uses project module artifacts for that repo context.

#### Scenario: Shadow guidance is actionable and emitted once per process

- **GIVEN** `<repo>/.specfact/modules/<module-id>` exists
- **AND** `<user-home>/.specfact/modules/<module-id>` exists
- **WHEN** module discovery runs repeatedly in the same process
- **THEN** CLI emits at most one user-facing warning that project scope takes precedence
- **AND** the warning includes actionable guidance to inspect origins and optionally clean a stale user-scope module copy.

### Requirement: Startup Module Freshness Guidance

Startup checks SHALL provide module freshness guidance for bundled modules across project and user scopes.

#### Scenario: Freshness check cadence

- **GIVEN** startup checks are enabled
- **WHEN** CLI version changed since last startup metadata check
- **THEN** module freshness check runs.

- **GIVEN** CLI version did not change
- **WHEN** last module freshness timestamp is less than 24 hours old
- **THEN** module freshness check is skipped.

- **GIVEN** CLI version did not change
- **WHEN** last module freshness timestamp is at least 24 hours old
- **THEN** module freshness check runs.

#### Scenario: Startup warns for stale project and user roots

- **GIVEN** bundled modules are missing or outdated in `<repo>/.specfact/modules`
- **OR** bundled modules are missing or outdated in `<user-home>/.specfact/modules`
- **WHEN** startup module freshness check runs
- **THEN** startup output includes actionable guidance with exact commands:
- **AND** project guidance uses `specfact module init --scope project`
- **AND** user guidance uses `specfact module init`.

### Requirement: Module List Bundled Availability View

`specfact module list` SHALL optionally show bundled modules that are available locally but not yet installed.

#### Scenario: Bundled-not-installed modules are shown in separate section

- **GIVEN** bundled module artifacts are present in package/workspace bundled sources
- **AND** one or more bundled modules are not discovered in active module roots
- **WHEN** the user runs `specfact module list` with the bundled-availability option
- **THEN** CLI output includes a separate table/section of bundled modules not yet installed.

#### Scenario: Bundled availability section includes install guidance

- **GIVEN** bundled-not-installed modules are shown
- **WHEN** section is rendered
- **THEN** output includes actionable hints to install bundled modules with:
- **AND** `specfact module init`
- **AND** `specfact module init --scope project`.

### Requirement: Scoped Module Install Resolution

`specfact module install` SHALL support scoped installation and resolve modules from bundled or marketplace sources.

#### Scenario: Install resolves bundled module by name

- **GIVEN** bundled module artifacts include `<module-id>`
- **WHEN** the user runs `specfact module install <module-id>`
- **THEN** install resolves `<module-id>` from bundled sources when available
- **AND** installs into selected scope root.

#### Scenario: Install supports explicit project scope

- **GIVEN** the user selects project scope
- **WHEN** `specfact module install <module-id>` runs
- **THEN** module is installed into `<repo>/.specfact/modules`
- **AND** command does not write into user root for that operation.

### Requirement: Scoped Module Uninstall Safety

`specfact module uninstall` SHALL support scoped uninstall and guard against ambiguous multi-scope removals.

#### Scenario: Uninstall requires explicit scope on multi-scope collision

- **GIVEN** `<module-id>` exists in both `<repo>/.specfact/modules` and `<user-home>/.specfact/modules`
- **WHEN** user runs `specfact module uninstall <module-id>` without explicit scope
- **THEN** command fails with guidance to choose `--scope user` or `--scope project`
- **AND** no module is removed.

#### Scenario: Uninstall removes only selected scope copy

- **GIVEN** `<module-id>` exists in both project and user scope roots
- **WHEN** user runs `specfact module uninstall <module-id> --scope project`
- **THEN** only `<repo>/.specfact/modules/<module-id>` is removed
- **AND** user-scope copy remains intact.

### Requirement: Module Denylist Enforcement

The system SHALL enforce a denylist check before installing or bootstrapping modules from any source.

#### Scenario: Denylisted module is blocked

- **GIVEN** `<module-id>` is present in configured denylist
- **WHEN** user runs `specfact module install <module-id>` or `specfact module init`
- **THEN** installation/bootstrap for `<module-id>` is blocked
- **AND** output includes clear security guidance.

### Requirement: Non-Official Publisher Trust Prompt

The system SHALL require explicit one-time trust acknowledgment for non-official publishers.

#### Scenario: First install of non-official module prompts for trust

- **GIVEN** module publisher is not official
- **AND** user has no stored trust decision for that publisher/module source
- **WHEN** user runs `specfact module install <module-id>`
- **THEN** command prompts for explicit trust acknowledgment
- **AND** stores trust decision for subsequent installs.

#### Scenario: Non-interactive install requires explicit trust flag

- **GIVEN** install runs in non-interactive mode
- **AND** trust acknowledgment does not yet exist
- **WHEN** user runs `specfact module install <module-id>`
- **THEN** command fails unless explicit trust override flag is provided.

### Requirement: Bundled Module Signature Verification

Shipped/bundled modules SHALL be verified by signature/checksum before install/bootstrap.

#### Scenario: Bundled signature verification passes

- **GIVEN** bundled module has valid signature/checksum metadata generated by release signing workflow
- **WHEN** user runs `specfact module init` or installs bundled module
- **THEN** module is installed/bootstrapped.

#### Scenario: Bundled signature verification fails

- **GIVEN** bundled module signature/checksum verification fails
- **WHEN** user runs `specfact module init` or installs bundled module
- **THEN** operation fails for that module
- **AND** module is not installed silently.

#### Scenario: Integrity fallback diagnostics are debug-only

- **GIVEN** bundled module checksum verification succeeds only after generated-file exclusions fallback
- **WHEN** verification runs in normal mode (without `--debug`)
- **THEN** fallback diagnostic details are not emitted as regular INFO output.

- **GIVEN** bundled module checksum verification succeeds only after generated-file exclusions fallback
- **WHEN** verification runs with global debug mode enabled (`--debug`)
- **THEN** fallback diagnostic details are emitted as debug-level diagnostics.

#### Scenario: Startup integrity failure shows user-friendly risk warning

- **GIVEN** module integrity verification fails during startup command registration
- **WHEN** CLI starts in normal mode (without `--debug`)
- **THEN** output shows a concise user-facing warning that the module was not loaded and may be tampered/outdated
- **AND** output includes mitigation guidance (for example `specfact module init`)
- **AND** raw checksum mismatch internals are not shown in normal startup logs.

#### Scenario: Startup integrity failure keeps raw diagnostics in debug mode

- **GIVEN** module integrity verification fails during startup command registration
- **WHEN** CLI starts with global debug mode enabled (`--debug`)
- **THEN** raw verification diagnostics (for example checksum mismatch details) are available in debug logging for troubleshooting.

### Requirement: Bundled Module Release Versioning and Signing Automation

Bundled module release tooling SHALL support module-level versioning independent of CLI package version and automate changed-module signing workflow.

#### Scenario: Changed modules are auto-bumped and signed

- **GIVEN** one or more bundled modules changed since a chosen git base ref
- **AND** changed module manifest version is unchanged
- **WHEN** release signing runs with changed-module automation enabled
- **THEN** only changed module manifests are selected
- **AND** changed module versions are incremented using configured semver bump strategy
- **AND** selected manifests are re-signed and re-verified in the same workflow.

#### Scenario: Unchanged modules keep version and signature metadata

- **GIVEN** bundled modules with no payload changes since selected git base ref
- **WHEN** changed-module automation runs
- **THEN** unchanged modules are not re-versioned and not re-signed.

#### Scenario: Module versions remain decoupled from CLI package version

- **GIVEN** CLI package version changes without payload change in a bundled module
- **WHEN** module signing/version checks run
- **THEN** bundled module version does not need to change
- **AND** module versioning is enforced only by module payload change semantics.

