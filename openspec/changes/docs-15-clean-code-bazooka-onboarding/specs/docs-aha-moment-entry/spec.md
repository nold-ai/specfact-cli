## MODIFIED Requirements

### Requirement: Quickstart leads to a scored code review aha moment

The quickstart SHALL let a new user run a scored review quickly and understand the next useful action after the first report.

#### Scenario: Quickstart explains cleanup handoff loop

- **WHEN** the quickstart explains `specfact code review run`
- **THEN** it SHALL include a short cleanup loop for AI-assisted code: run JSON, inspect cleanup forecast and AI-bloat index, hand remediation packets to an AI IDE, and re-run review
- **AND** it SHALL link to the modules AI bloat quickstart for exact command and report details
