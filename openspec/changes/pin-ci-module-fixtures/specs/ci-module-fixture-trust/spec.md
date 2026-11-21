## ADDED Requirements

### Requirement: Pin module fixtures before CI checkout

Default-branch-capable validation jobs SHALL check out the official module repository at the reviewed literal commit. Fixture lock verification SHALL remain in place before a job executes or exposes the module sources to validation.

#### Scenario: Scheduled and manual validation select the reviewed revision

- **WHEN** the orchestrator, contract check or docs check acquires a module fixture
- **THEN** its checkout uses the literal repository and commit recorded in the corresponding lock with credential persistence disabled
