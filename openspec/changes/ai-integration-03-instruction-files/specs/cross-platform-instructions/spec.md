## ADDED Requirements

### Requirement: Cross Platform Instructions
The system SHALL generate platform-specific instruction files that reference the canonical SpecFact skill behavior.

#### Scenario: Multi-platform setup command writes instruction files
- **GIVEN** `specfact ide setup --platforms cursor,copilot,claude,windsurf`
- **WHEN** setup runs
- **THEN** platform instruction files are generated in expected locations
- **AND** each file references the same canonical SpecFact workflow entry points.

#### Scenario: Regeneration is idempotent
- **GIVEN** instruction files already exist
- **WHEN** setup is re-run without behavior changes
- **THEN** files are updated deterministically
- **AND** no duplicate instruction blocks are introduced.
