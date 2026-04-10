# lazy-loading Specification

## Purpose

TBD - created by archiving change arch-01-cli-modular-command-registry. Update Purpose after archive.

## Requirements

### Requirement: Only Invoked Command Module Loaded at Runtime

The root CLI application SHALL NOT import command modules at top level. It SHALL build the Typer tree from the registry (or cached metadata for help) and load a command module only when that command is invoked (or when its help is requested).

**Rationale**: Reduces startup time and avoids merge conflicts in a single cli.py file.

#### Scenario: Invoke Single Command Without Loading Others

**Given**: SpecFact CLI is started (e.g. `specfact init --help` or `specfact init`)

**When**: The user invokes only the "init" command (or requests help for "init")

**Then**: Only the module providing the "init" command is loaded; no other command modules (e.g. backlog, sync, validate) are imported

**Acceptance Criteria**:

- cli.py does not contain top-level imports of command modules (e.g. `from specfact_cli.commands import init, backlog_commands, ...`)
- Root app adds command groups by name from registry; each group is resolved via CommandRegistry.get_typer(name) on first use (lazy callback or dynamic add)
- Integration test or smoke test: run `specfact init --help` and assert exit 0; optional: assert no import of backlog_commands or other heavy modules during that run (e.g. via import hooks or coverage)

#### Scenario: Same CLI Surface After Refactor

**Given**: The refactor is complete

**When**: User runs `specfact --help`, `specfact init --help`, `specfact backlog --help` (and other commands as before)

**Then**: Output and exit codes match pre-refactor behavior; all existing command names and help strings remain available

**Acceptance Criteria**:

- No removal or renaming of commands
- Help text for each command group unchanged from user perspective
- Contract tests or CLI tests that assert key commands and --help exit 0 remain passing
