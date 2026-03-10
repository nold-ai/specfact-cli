## ADDED Requirements

### Requirement: n8n F-4 Workflow Using specfact code review run with Three-Branch Routing
The system SHALL replace `codex review` in n8n F-4 with `specfact code review run --json`, route on PASS/WARN/BLOCK, and update the reward ledger after every execution.

#### Scenario: F-4 routes PASS correctly
- **GIVEN** changed files have no blocking violations
- **WHEN** F-4 runs `specfact code review run --json`
- **THEN** `overall_verdict="PASS"` and the workflow routes to the PASS branch
- **AND** `specfact code review ledger update` is called once

#### Scenario: F-4 BLOCK verdict stops the workflow
- **GIVEN** changed files have blocking violations
- **WHEN** F-4 runs
- **THEN** `overall_verdict="FAIL"` and a human notification is triggered with no git commit made

#### Scenario: F-4 WARN verdict continues with advisory
- **GIVEN** changed files have warnings but no blocking errors
- **WHEN** F-4 runs
- **THEN** `overall_verdict="PASS_WITH_ADVISORY"` and workflow continues with ledger updated

#### Scenario: house_rules injected into F-2 container
- **GIVEN** F-2 launches a coding container
- **WHEN** the container environment is set up
- **THEN** `HOUSE_RULES` env var is set to the skill content (truncated to 2000 chars if needed)
- **AND** the coding CLI receives `context.house_rules` in stdin JSON
