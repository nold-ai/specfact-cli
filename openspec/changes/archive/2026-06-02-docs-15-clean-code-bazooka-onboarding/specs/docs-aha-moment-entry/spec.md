## ADDED Requirements

### Requirement: Quickstart leads to a scored code review aha moment

The quickstart SHALL let a new user run a scored review quickly and understand the next useful action after the first report.

#### Scenario: Quickstart explains cleanup handoff loop

- **WHEN** the quickstart explains `specfact code review run`
- **THEN** it SHALL include a short cleanup loop for AI-assisted code: run JSON, inspect cleanup forecast and AI-bloat index, hand remediation packets to an AI IDE, and re-run review
- **AND** it SHALL link to the modules AI bloat quickstart for exact command and report details

#### Scenario: Docs entry points share the AI-bloat defense hook

- **WHEN** users read `docs/index.md`, `docs/README.md`, or the getting-started landing page
- **THEN** those surfaces SHALL use the same AI-bloat defense first-contact story as the README
- **AND** they SHALL route users to the quickstart before deep module topology
- **AND** they SHALL preserve the docs/modules ownership boundary for exact Code Review command and schema details
