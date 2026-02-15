## MODIFIED Requirements

### Requirement: Daily Standup
Daily standup output SHALL include requirement and architecture blockers when present.

#### Scenario: Standup reports upstream blockers before technical tasks
- **GIVEN** tasks are blocked by missing requirement or architecture decisions
- **WHEN** standup summary is generated
- **THEN** blockers are listed under a business/architecture blocker section
- **AND** unresolved upstream blockers are prioritized above downstream code tasks.
