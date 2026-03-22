## ADDED Requirements

### Requirement: Backlog Auth Commands
When the backlog bundle is installed, the CLI SHALL expose `specfact backlog auth` commands that reuse the central SpecFact auth-token interface rather than duplicating provider token storage logic.

#### Scenario: Provider auth commands reuse the shared token store
- **GIVEN** the backlog bundle provides `specfact backlog auth azure-devops` and `specfact backlog auth github`
- **WHEN** a user authenticates through one of those commands
- **THEN** the command stores and retrieves credentials through the shared `specfact_cli.utils.auth_tokens` interface
- **AND** provider identifiers remain compatible with existing stored tokens

#### Scenario: Status and clear commands reflect shared token state
- **GIVEN** auth tokens exist or have been cleared for supported backlog providers
- **WHEN** `specfact backlog auth status` or `specfact backlog auth clear` is executed
- **THEN** the command reports or clears the shared token state for the requested provider set
- **AND** no backlog-specific duplicate token store is introduced
