## MODIFIED Requirements

### Requirement: Core CLI reference pages exist

The system SHALL provide dedicated reference pages for core CLI commands.

#### Scenario: Init reference page documents all subcommands and options

- **GIVEN** the docs/core-cli/init.md page exists
- **WHEN** a user reads the page
- **THEN** it documents: specfact init, init --profile, init --install, init ide, init --install-deps
- **AND** all documented commands match the actual --help output.

#### Scenario: Init ide exports match target integration model

- **GIVEN** prompt sources are available from core or installed modules
- **WHEN** `specfact init ide` exports to a slash-command target such as Cursor, VS Code, or Claude commands
- **THEN** it writes one prompt file per workflow into the target command/prompt directory.
- **WHEN** `specfact init ide` exports to a skill-based target such as Codex CLI, Claude Code Skills, or Mistral Vibe
- **THEN** it writes grouped capability-oriented `<skill>/SKILL.md` files per selected source/module
- **AND** it does not create one `SKILL.md` folder per slash-command prompt.

#### Scenario: Module reference page documents all subcommands

- **GIVEN** the docs/core-cli/module.md page exists
- **WHEN** a user reads the page
- **THEN** it documents: module install, module uninstall, module list, module show, module search, module upgrade, module alias, module add-registry, module list-registries, module remove-registry, module enable, module disable
- **AND** all documented commands match the actual --help output.

#### Scenario: Upgrade reference page documents the command

- **GIVEN** the docs/core-cli/upgrade.md page exists
- **WHEN** a user reads the page
- **THEN** it documents the specfact upgrade command and its options.

#### Scenario: Reference docs are checked against generated command overview

- **GIVEN** a core CLI reference page, prompt, template, or guidance string contains a `specfact` command example
- **WHEN** docs command validation runs
- **THEN** the example is checked against the generated command overview
- **AND** stale flat shims and invalid option ordering fail validation
- **AND** no reference page is excluded from command validation unless it is explicitly marked as historical migration material.
