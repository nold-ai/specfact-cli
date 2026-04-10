## ADDED Requirements

### Requirement: Mcp Server

The system SHALL expose a bounded set of high-value MCP tools for validation, compatibility, coverage, and fix guidance.

#### Scenario: MCP tool returns summarized result with reference

- **GIVEN** a validation MCP tool invocation
- **WHEN** execution completes
- **THEN** response returns concise summary metrics
- **AND** includes a link or path to the full report artifact.

#### Scenario: Tool surface remains intentionally small

- **GIVEN** MCP server configuration
- **WHEN** server starts
- **THEN** only approved core tools are exposed
- **AND** raw bulk document dumping is not the default response behavior.
