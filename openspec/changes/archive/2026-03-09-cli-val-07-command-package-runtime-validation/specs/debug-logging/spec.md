## ADDED Requirements

### Requirement: Module Discovery Diagnostics Are Debug-Gated

The system SHALL keep internal module-discovery diagnostics out of normal command output and SHALL surface them only through debug-mode channels unless the message is actionable for the user.

#### Scenario: Internal discovery diagnostics stay hidden when debug is off

- **GIVEN** `--debug` is not enabled
- **AND** command startup performs module discovery and protocol inspection
- **WHEN** discovery observes partial protocol compliance, legacy protocol state, or duplicate observations of the canonical user module root
- **THEN** those diagnostics are not shown on stdout or stderr
- **AND** they do not appear as INFO or WARNING output during normal command execution.

#### Scenario: Internal discovery diagnostics are available when debug is on

- **GIVEN** `--debug` is enabled
- **WHEN** command startup performs module discovery and protocol inspection
- **THEN** internal discovery diagnostics may be emitted through debug logging
- **AND** the diagnostics are routed through established debug-mode channels rather than normal non-debug output.

#### Scenario: Actionable warnings remain visible without debug

- **GIVEN** `--debug` is not enabled
- **WHEN** module discovery encounters a security, trust, integrity, or real scope-precedence problem that requires user action
- **THEN** the CLI still emits an actionable warning
- **AND** the warning text explains the remediation instead of exposing raw internal diagnostics.

#### Scenario: Routine bundled dependency satisfaction stays non-warning

- **GIVEN** `--debug` is not enabled
- **AND** a bundled module upgrade sees that a declared bundled dependency is already installed at the required version
- **WHEN** the upgrade completes without conflict, trust, or integrity problems
- **THEN** normal output does not emit a warning for that already-satisfied dependency
- **AND** any optional trace for the satisfied dependency is routed to debug or informational channels instead.

#### Scenario: Bridge logger lines stay out of normal console output

- **GIVEN** `--debug` is not enabled
- **WHEN** internal bridge or registry code records non-actionable informational or warning diagnostics through the shared logger
- **THEN** those raw logger lines do not appear in the user's console output
- **AND** only explicitly formatted user-facing warnings remain visible when the user must take action.
