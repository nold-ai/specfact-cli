## ADDED Requirements

### Requirement: Fresh wheel resolution preserves CLI startup

The distributed SpecFact CLI wheel SHALL start with dependencies resolved from its package metadata without an additional Typer constraint.

#### Scenario: A fresh uvx invocation starts the CLI

- **GIVEN** a rebuilt SpecFact wheel and an isolated uvx environment
- **WHEN** uvx resolves the wheel dependencies and invokes the console script
- **THEN** `--version` and `--help` succeed
- **AND** `module list --help` renders the core module command options.

#### Scenario: Typer injects context for registered callbacks

- **GIVEN** a registered command callback with a Click context annotation and a CLI option
- **WHEN** a user invokes that command with the option
- **THEN** Typer supplies an active context and passes the option value to the callback.

#### Scenario: The command inventory describes Typer positional arguments

- **GIVEN** Typer commands with a required positional argument or an optional variadic argument
- **WHEN** the inventory inspects the generated command parameters
- **THEN** it preserves the argument name, required status, and arity.
