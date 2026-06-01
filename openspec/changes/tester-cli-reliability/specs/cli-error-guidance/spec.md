## ADDED Requirements

### Requirement: CLI Errors Show Relevant Help And Missing Information

The CLI SHALL render actionable help for unknown commands, missing subcommands, and missing required parameters across core and loaded module command groups.

#### Scenario: Unknown root command suggests recovery

- **GIVEN** a user invokes an unknown root command such as `specfact hello`
- **WHEN** command resolution fails
- **THEN** the output includes the root help context
- **AND** it states that `hello` is not a valid command
- **AND** it suggests nearby valid command groups or the command used to list commands
- **AND** the command exits with a usage-error status.

#### Scenario: Missing subcommand on command group

- **GIVEN** a command group has no default action
- **WHEN** the user invokes the group without a subcommand
- **THEN** the output includes that group's help
- **AND** it states that a subcommand is required
- **AND** it lists or points to the available subcommands
- **AND** the command exits with a usage-error status.

#### Scenario: Missing required parameter on leaf command

- **GIVEN** a leaf command requires one or more arguments or options
- **WHEN** the user invokes the command without those required parameters
- **THEN** the output includes that command's help
- **AND** it names each missing required parameter using its CLI spelling
- **AND** it shows the canonical invocation shape
- **AND** the command exits with a usage-error status.

#### Scenario: Explicit help remains successful

- **GIVEN** a user invokes any command or command group with `--help`
- **WHEN** help rendering succeeds
- **THEN** the command exits successfully
- **AND** no missing-parameter or missing-subcommand error is emitted.
