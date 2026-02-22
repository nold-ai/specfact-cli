## ADDED Requirements

### Requirement: CLI Scenario Prompt Template

The system SHALL provide a prompt template that generates CLI behavior scenario YAML, anti-pattern catalog, and acceptance test content for a given command.

#### Scenario: Prompt generates valid scenario YAML

- **GIVEN** a CLI command signature (name, arguments, options)
- **WHEN** the prompt template is applied by a copilot
- **THEN** the output includes a valid YAML scenario file conforming to the cli-val-01 schema
- **AND** the file contains at least 3 pattern scenarios and 3 anti-pattern scenarios.

#### Scenario: Prompt generates anti-pattern catalog

- **GIVEN** a CLI command that accepts file paths, enum values, and optional flags
- **WHEN** the prompt template is applied
- **THEN** anti-patterns are generated for: missing required args, invalid enum values, nonexistent paths, and forbidden combinations
- **AND** each anti-pattern includes expected non-zero exit and error pattern.

#### Scenario: Prompt generates Markdown acceptance test

- **GIVEN** a CLI command with a documented workflow
- **WHEN** the prompt template is applied
- **THEN** the output includes a Markdown-formatted acceptance test showing the command workflow as a terminal session
- **AND** the acceptance test includes expected output patterns.

### Requirement: Generate Test-Prompt Integration

The system SHALL extend the existing `specfact generate test-prompt` workflow to offer CLI scenario templates.

#### Scenario: Workflow detects CLI command and offers scenario template

- **GIVEN** the user runs `specfact generate test-prompt` targeting a file containing a Typer command
- **WHEN** the workflow detects `@app.command()` decorators
- **THEN** it offers the CLI behavior scenario template as an option alongside unit test templates.

### Requirement: Convention Enforcement Documentation

The system SHALL document the convention that every OpenSpec change modifying CLI commands must include updated scenario files.

#### Scenario: Convention is documented in contributor guide

- **GIVEN** the documentation site at docs.specfact.io
- **WHEN** a contributor reads the CLI validation guide
- **THEN** the guide states that scenario files are required for CLI command changes
- **AND** provides examples of how to generate scenarios using the copilot workflow.
