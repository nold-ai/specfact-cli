## ADDED Requirements

### Requirement: Agent Skill Spec Intelligence
The system SHALL provide a skill-first integration that directs AI agents to SpecFact workflows with low context overhead.

#### Scenario: Skill instructs agent to run deterministic CLI checks
- **GIVEN** skill is activated for PR or change analysis
- **WHEN** agent follows skill guidance
- **THEN** agent invokes commands such as `specfact validate`, `specfact trace show`, and `specfact requirements list`
- **AND** output references evidence paths instead of embedding large raw artifacts.

#### Scenario: Skill content remains lightweight at rest
- **GIVEN** skill metadata is loaded by an IDE agent
- **WHEN** idle context is measured
- **THEN** base skill content remains compact
- **AND** detailed guidance is loaded only on activation.
