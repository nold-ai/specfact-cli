## ADDED Requirements

### Requirement: Isolate the opt-in Semgrep installation

SpecFact SHALL exclude Semgrep and its scanner-only dependencies from the core wheel and shared Python lock. Independent Static Analysis SHALL audit a hash-locked Semgrep dependency set before installing or running it in a separate environment. A failed audit SHALL fail the job. The existing Semgrep rules, findings baseline, and Bandit check SHALL remain in use.

#### Scenario: Shared installations omit the scanner

- **WHEN** the core wheel or shared CI environment is resolved
- **THEN** the Python package and lock do not select Semgrep, MCP, or wcmatch

#### Scenario: The Semgrep check uses audited packages

- **WHEN** Independent Static Analysis runs
- **THEN** it first audits the separately locked scanner graph
- **AND** it installs only hash-verified wheels in its own environment and runs the existing scan after a successful audit
