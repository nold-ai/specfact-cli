# ledger-commands Specification

## Purpose

TBD - created by archiving change code-review-06-reward-ledger. Update Purpose after archive.

## Requirements

### Requirement: Ledger CLI Subcommands for Update, Status, and Reset

The system SHALL provide `specfact code review ledger update|status|reset` subcommands for managing the reward ledger from the terminal.

#### Scenario: ledger update reads ReviewReport JSON from stdin

- **GIVEN** `specfact code review run --json` output piped to `specfact code review ledger update`
- **WHEN** the command executes
- **THEN** `LedgerClient.record_run` is called with the parsed `ReviewReport` and exit code is 0

#### Scenario: ledger update with invalid JSON exits with error

- **GIVEN** invalid JSON is provided on stdin
- **WHEN** `specfact code review ledger update` runs
- **THEN** an error message is printed to stderr and exit code is 1

#### Scenario: ledger status prints current state

- **GIVEN** the ledger has `coins=7.3`, `streak_pass=2`, `last_verdict="PASS"`
- **WHEN** `specfact code review ledger status` runs
- **THEN** output includes `7.30` coins, `2` pass streak, and `PASS` last verdict

#### Scenario: ledger reset without --confirm refuses deletion

- **GIVEN** `specfact code review ledger reset` is run without `--confirm`
- **WHEN** the command executes
- **THEN** an error message asking for `--confirm` is printed and nothing is deleted

#### Scenario: ledger reset with --confirm clears local ledger

- **GIVEN** `specfact code review ledger reset --confirm` is run
- **WHEN** the command executes
- **THEN** `~/.specfact/ledger.json` is cleared and exit code is 0
