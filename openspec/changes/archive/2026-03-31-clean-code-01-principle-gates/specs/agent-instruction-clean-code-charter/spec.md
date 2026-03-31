## ADDED Requirements

### Requirement: Agent Instruction Clean-Code Charter
The repository SHALL expose the 7-principle clean-code charter consistently across its instruction surfaces without creating drift-prone duplicate sources of truth.

#### Scenario: Core instruction surfaces reference the charter consistently
- **GIVEN** a contributor opens `AGENTS.md`, `CLAUDE.md`, `.cursor/rules/clean-code-principles.mdc`, or `.github/copilot-instructions.md`
- **WHEN** they inspect clean-code guidance
- **THEN** each surface points to the same clean-code charter semantics
- **AND** any shorter alias surface references the canonical charter rather than redefining it independently

#### Scenario: Generated IDE aliases stay lightweight
- **GIVEN** platform-specific instruction files are generated from `ai-integration-03-instruction-files`
- **WHEN** clean-code guidance is included
- **THEN** the generated file contains a short clean-code alias reference
- **AND** the full charter text is not duplicated into every generated alias
