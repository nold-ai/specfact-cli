# installed-runtime-module-discovery Specification

## Purpose

TBD - created by archiving change backlog-core-04-installed-runtime-discovery-and-add-prompt. Update Purpose after archive.
## Requirements
### Requirement: Module Discovery Roots

The system SHALL discover and load module packages consistently between development and installed runtime contexts.

#### Scenario: Installed runtime loads dependent module packages

- **GIVEN** user-scope modules `nold-ai/specfact-project` and `nold-ai/specfact-codebase` are installed and enabled
- **AND** no sibling `specfact-cli-modules` source checkout contributes bundle paths to `sys.path`
- **WHEN** the user invokes `specfact code --help`
- **THEN** the codebase module command app loads from the installed module artifact
- **AND** imports of installed dependency packages such as `specfact_project` resolve without manual `PYTHONPATH`
- **AND** the command help includes codebase subcommands such as `import`, `analyze`, `drift`, `validate`, and `repro`

#### Scenario: Development source paths do not mask installed-runtime validation

- **GIVEN** tests configure explicit installed module roots
- **AND** development-only sibling module source paths are disabled for that runtime
- **WHEN** module command loading is validated
- **THEN** success depends on the installed module artifacts under the configured roots
- **AND** missing installed dependencies fail the validation instead of being satisfied by a sibling checkout

