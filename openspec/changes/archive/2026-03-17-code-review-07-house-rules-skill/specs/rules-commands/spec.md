## ADDED Requirements

### Requirement: House Rules CLI Subcommands for Show, Update, and Init

The system SHALL provide `specfact code review rules show|update|init` subcommands for managing the house rules skill file.

#### Scenario: rules show prints current SKILL.md content

- **GIVEN** `skills/specfact-code-review/SKILL.md` exists
- **WHEN** `specfact code review rules show` is run
- **THEN** the full content is printed to stdout and exit code is 0

#### Scenario: rules show with missing SKILL.md prints helpful error

- **GIVEN** no SKILL.md exists at the expected path
- **WHEN** `specfact code review rules show` is run
- **THEN** an error message suggesting `rules init` is printed and exit code is 1

#### Scenario: rules update re-derives TOP VIOLATIONS from ledger

- **GIVEN** the ledger has 20 runs with violation `C901` appearing 5 times
- **WHEN** `specfact code review rules update` is run
- **THEN** `C901` appears in TOP VIOLATIONS and the version header is incremented

#### Scenario: rules init creates default skill for new project

- **GIVEN** no SKILL.md exists
- **WHEN** `specfact code review rules init` is run
- **THEN** SKILL.md is created with default content and exit code is 0
