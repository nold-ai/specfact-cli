## MODIFIED Requirements

### Requirement: README gives first-contact users a fast validation path

The README SHALL give first-contact users a concise path to run SpecFact on a real repository and understand the most important output.

#### Scenario: README introduces cleanup forecast as a value path

- **WHEN** the Code Review bundle supports cleanup forecasts and AI IDE remediation packets
- **THEN** the README SHALL mention that SpecFact can quantify likely cleanup impact for AI-assisted codebases
- **AND** it SHALL describe the JSON report as the portable handoff artifact for AI IDE cleanup
- **AND** it SHALL avoid presenting `ai_bloat` as AI-authorship detection
